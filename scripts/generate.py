import os
import time
from PIL import Image
from pathlib import Path
from contextlib import closing

import gradio as gr

from modules.shared import opts
from modules import shared, progress
from modules.ui import plaintext_to_html
from modules.call_queue import queue_lock
from modules import scripts
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
        self.process_count = 0
        self.process_curr = 0
        self.iter_images = None
        self.images_list = []
        self.default_args = None
        self.show_log = plaintext_to_html("", classname="comments")
        self._init_data()

    def _init_data(self):
        self.reset_outputs_info()
        self.script_runner = scripts.scripts_txt2img
        self.init_default_script_args()

    def init_default_script_args(self):
        # if not self.script_runner.scripts:
        #     self.script_runner.initialize_scripts(False)
        #     ui.create_ui()

        last_arg_index = 1
        for script in self.script_runner.scripts:
            if last_arg_index < script.args_to:
                last_arg_index = script.args_to
        script_args = [None] * last_arg_index
        script_args[0] = 0

        with gr.Blocks(analytics_enabled=False):
            with gr.Row(visible=False):
                for script in self.script_runner.scripts:
                    if script.ui(script.is_img2img):
                        ui_default_values = []
                        for elem in script.ui(script.is_img2img):
                            ui_default_values.append(elem.value)
                        script_args[script.args_from:script.args_to] = ui_default_values
        self.default_args = script_args

    def reset_outputs_info(self):
        self.out_image = None
        self.out_generation_info_js = ""
        self.out_info = ""
        self.out_comments = ""

    def set_out_comments(self, out_comments=""):
        self.out_comments = plaintext_to_html(out_comments, classname="comments")

    @property
    def outputs_info(self):
        return self.out_image, self.out_generation_info_js, self.out_info, self.out_comments

    def up(self, filepath):

        geninfo, _ = read_info_from_image(Image.open(filepath))
        geninfo = parse_generation_parameters(geninfo)

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
                    p.scripts = self.script_runner
                    p.outpath_samples = self.output_floder
                    p.outpath_grids = opts.outdir_txt2img_grids

                    shared.state.begin(job=self.id_task)
                    p.script_args = tuple(self.default_args)
                    processed = process_images(p)
                    progress.record_results(self.id_task, processed)

            finally:
                progress.finish_task(self.id_task)
                shared.state.end()
                shared.total_tqdm.clear()

        generation_info_js = processed.js()

        self.out_image = processed.images
        self.out_generation_info_js = generation_info_js
        self.out_info = plaintext_to_html(processed.info)
        self.out_comments = plaintext_to_html(processed.comments, classname="comments")

    def interrupt(self):
        self.flag = False
        self.process_curr = 0
        self.process_count = 0
        # self.id_task = None
        self.iter_images = None
        self.images_list = []
        shared.state.interrupt()
        return "Stopped", self.process_count, self.process_curr

    def fake_up(self):

        progress.add_task_to_queue(self.id_task)
        with queue_lock:
            progress.start_task(self.id_task)
            shared.state.begin(job=self.id_task)

            time.sleep(3.5)
            progress.finish_task(self.id_task)
            shared.state.end()
            shared.total_tqdm.clear()

        self.out_image = None
        self.out_generation_info_js = ""
        self.out_info = ""

    def iterImages(self):
        for filepath in self.images_list:
            if not self.flag:
                return
            yield filepath

    def get_next_image(self):
        if not self.iter_images:
            return None
        try:
            return next(self.iter_images)
        except StopIteration:
            return None

    def validate_image_type(self, filename):
        ext = filename.split(".")[-1]
        if ext not in ["jpg", "jpeg", "png"]:
            return False
        return True

    def validate_images_in_folder(self, input_folder, output_floder):

        path = Path(input_folder)
        if input_folder == "" or not path.is_dir():
            return "请输入正确的输入文件夹路径"
        out_path = Path(output_floder)
        if output_floder == "" or not out_path.is_dir():
            return "请输入正确的输出文件夹路径"

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
            return "未找到有效的图片"

        return "valid"

    def first_start(
            self, id_task, input_folder, output_floder, select_upscaler, select_upscaler_visibility, redraw_amplitude
    ):

        if "repetitive" in id_task:
            return id_task.replace("repetitive", ""), self.process_count, self.process_curr, self.out_info, self.out_comments

        self.images_list = []
        self.id_task = "Starting"
        self.select_upscaler = select_upscaler
        self.select_upscaler_visibility = select_upscaler_visibility
        self.redraw_amplitude = redraw_amplitude

        valid_result = self.validate_images_in_folder(input_folder, output_floder)
        self.process_curr = 0
        self.process_count = len(self.images_list)

        if valid_result != "valid":
            self.id_task = "Stopping"
            self.set_out_comments(f'启动错误: {valid_result}')

        elif self.process_count > 0:
            self.flag = True
            self.reset_outputs_info()
            self.iter_images = self.iterImages()

        else:
            self.id_task = "Stopping"

        return self.id_task, self.process_count, self.process_curr, self.out_info, self.out_comments

    def loop_start(self, id_task, process_count, process_curr):

        self.process_count = int(process_count)
        self.process_curr = int(process_curr)

        if id_task == "WaitStart":
            return *self.outputs_info, "WaitStart2", self.process_count, 0

        if id_task == "Stopping":
            return *self.outputs_info, "Stopped", self.process_count, 0

        self.id_task = id_task
        filepath = self.get_next_image()
        if not filepath:
            self.interrupt()
            self.id_task = "Stopping"
            self.process_count = 0
            return *self.outputs_info, self.id_task, self.process_count, 0

        if not os.path.exists(filepath):
            self.fake_up()
            self.set_out_comments(f"Skip, not find file: {filepath}")
            return *self.outputs_info, self.id_task, self.process_count, self.process_curr

        # print(f"({self.process_curr}/{self.process_count})开始处理图片...{filepath}")
        self.up(filepath)

        return *self.outputs_info, self.id_task, self.process_count, self.process_curr
