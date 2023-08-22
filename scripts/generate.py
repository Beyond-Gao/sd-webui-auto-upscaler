import os
import time
from pathlib import Path
from PIL import Image
from contextlib import closing

from modules.shared import opts
from modules import shared, progress
from modules.ui import plaintext_to_html
from modules.call_queue import queue_lock
from modules.scripts import scripts_txt2img
from modules.images import read_info_from_image
from modules.generation_parameters_copypaste import parse_generation_parameters
from modules.processing import StableDiffusionProcessingTxt2Img, process_images


class LoopUpscaler:

    def __init__(self) -> None:
        self.input_folder = None
        self.output_floder = None
        self.select_upscaler = None
        self.select_upscaler_visibility = None
        self.redraw_amplitude = None

        self.flag = True
        self.id_task = "0"
        self.img_geninfo_list = []
        self.img_geninfo_num = 0
        self.outputs_info = [None, None, None, None]

        self.process_count = 0
        self.process_curr = 0
        self.iter_images = None
        self.images_list = []

    def validate_image_type(self, filename):
        suffix = filename.split(".")[-1]
        if suffix not in ["jpg", "jpeg", "png"]:
            return False
        return True

    def validate_images_in_folder(self, input_folder, output_floder):

        path = Path(input_folder)
        print(f'path: {path}')
        if input_folder == "" or not path.is_dir():
            print("请输入正确的输入文件夹路径")
            return 0
        out_path = Path(output_floder)
        print(f'out_path: {out_path}')
        if output_floder == "" or not out_path.is_dir():
            print("请输入正确的输出文件夹路径")
            return 0

        self.input_folder = input_folder
        self.output_floder = output_floder

        files = os.listdir(path)
        for filename in files:

            if not self.validate_image_type(filename):
                continue

            # TODO: 对比输出目录，忽略已高清修复的文件
            # TODO: 获取子文件夹下的所有图片

            self.images_list.append(path.joinpath(filename))

        if len(self.images_list) <= 0:
            print("未找到有效的图片")
            return 0

    def up(self, filepath):

        geninfo, _ = read_info_from_image(Image.open(filepath))
        geninfo = parse_generation_parameters(geninfo)

        # print(f'geninfo: {geninfo}')

        args = {
            "prompt": geninfo["Prompt"],  # 提示词
            "negative_prompt": geninfo["Negative prompt"],  # 负面提示词
            "steps": int(geninfo["Steps"]),  # 步数
            "sampler_name": geninfo["Sampler"],  # 采样方法名称
            "cfg_scale": float(geninfo["CFG scale"]),  # 提示词引导系数
            "seed": int(geninfo["Seed"]),  # 随机数种子
            "width": int(geninfo["Size-1"]),
            "height": int(geninfo["Size-2"]),
            # "denoising_strength": float(geninfo["Denoising strength"]),  # 重绘幅度？
        }

        args["enable_hr"] = True  # 是否开启放大
        args["hr_scale"] = self.select_upscaler_visibility  # 放大倍数
        args["hr_upscaler"] = self.select_upscaler  # 放大算法方法名
        args["denoising_strength"] = self.redraw_amplitude  # 重绘幅度
        args["hr_resize_x"] = 0  # 将宽度调整为
        args["hr_resize_y"] = 0  # 将高度调整为

        progress.add_task_to_queue(self.id_task)

        with queue_lock:
            progress.start_task(self.id_task)

            try:
                with closing(StableDiffusionProcessingTxt2Img(sd_model=shared.sd_model, **args)) as p:
                    p.scripts = scripts_txt2img
                    p.outpath_samples = self.output_floder
                    p.outpath_grids = opts.outdir_txt2img_grids

                    shared.state.begin(job=self.id_task)
                    p.script_args = ()  # 脚本的args
                    processed = process_images(p)
                    progress.record_results(self.id_task, processed)

            finally:
                progress.finish_task(self.id_task)
                shared.state.end()
                shared.total_tqdm.clear()

        generation_info_js = processed.js()
        self.outputs_info = [
            processed.images,
            generation_info_js,
            plaintext_to_html(processed.info),
            plaintext_to_html(processed.comments, classname="comments"),
        ]

    def interrupt(self):
        print("click: interrupt")
        self.flag = False
        self.process_curr = 0
        self.process_count = 0
        # self.id_task = None
        self.iter_images = None
        self.images_list = []
        shared.state.interrupt()
        return "stopped", 0, 0

    def iterImages(self):
        for filepath in self.images_list:
            if not self.flag:
                return
            yield filepath

    def get_next_image(self):
        try:
            return next(self.iter_images)
        except StopIteration:
            return None

    def fake_up(self):

        progress.add_task_to_queue(self.id_task)

        with queue_lock:
            progress.start_task(self.id_task)
            shared.state.begin(job=self.id_task)

            time.sleep(3.5)
            progress.finish_task(self.id_task)
            shared.state.end()
            shared.total_tqdm.clear()

        self.outputs_info = [
            None,
            "",
            "",
            "",
        ]

    def loop_start(self, id_task, process_count, process_curr):

        self.process_count = int(process_count)
        self.process_curr = int(process_curr)

        print(f'loop_start: {id_task}  {self.process_count}  {self.process_curr} {time.time()}')

        if id_task == "waitStart":
            print("等待任务开始")
            return self.outputs_info + [id_task, self.process_count, 0]

        if id_task == "stopping":
            print("结束任务！")
            return self.outputs_info + ["stopped", self.process_count, 0]

        self.id_task = id_task

        filepath = self.get_next_image()
        if not filepath:
            print("任务已完成。")
            self.id_task = "stopping"
            self.process_count = 0
            return self.outputs_info + [self.id_task, self.process_count, 0]

        if not os.path.exists(filepath):
            return self.outputs_info + [self.id_task, self.process_count, self.process_curr]

        print(f"({self.process_curr}/{self.process_count})开始处理图片...{filepath}")
        self.up(filepath)
        # self.fake_up()

        # print(f'return: {self.outputs_info + [self.id_task, self.process_count, self.process_curr]}')
        return self.outputs_info + [self.id_task, self.process_count, self.process_curr]

    def first_start(self, id_task, input_folder, output_floder, select_upscaler, select_upscaler_visibility,
                    redraw_amplitude):

        if "repetitive" in id_task:
            return id_task.replace("repetitive", ""), self.process_count, self.process_curr

        if not input_folder:
            input_folder = r"E:\NovelAI\outputs\ls\au\input"
        if not output_floder:
            output_floder = r"E:\NovelAI\outputs\ls\au\ouput"

        self.images_list = []
        self.id_task = "starting"
        self.select_upscaler = select_upscaler
        self.select_upscaler_visibility = select_upscaler_visibility
        self.redraw_amplitude = redraw_amplitude

        self.validate_images_in_folder(input_folder, output_floder)

        self.process_curr = 0
        self.process_count = len(self.images_list)

        if self.process_count > 0:
            self.flag = True
            self.iter_images = self.iterImages()
        else:
            self.id_task = "stopping"

        print(f'first_start return: {self.id_task, self.process_count, self.process_curr}')
        return self.id_task, self.process_count, self.process_curr

    # def run(self, id_task, input_folder, output_floder):
    #     self.validate_images_in_folder(input_folder, output_floder)

    #     # self.loop_start()

    #     # 返回待处理的总数量
    #     return id_task, len(self.images_list)

