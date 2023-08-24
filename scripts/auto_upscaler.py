import gradio as gr

from modules import shared
from modules import script_callbacks
from modules.ui_components import FormRow
from scripts.au_util import AuUtils
from scripts.generate import LoopUpscaler
from modules.scripts import scripts_txt2img
import modules

folder_symbol = '\U0001f4c2'  # 📂


# add more UI components (cf. https://gradio.app/docs/#components)
def on_ui_tabs():
    self_type = "auto_upscaler"

    def bind_func(
            submit, interrupt
    ):

        l = LoopUpscaler()

        submit.click(
            fn=l.first_start,
            _js="auFirstStart",
            inputs=[
                id_task,
                task_info,
                input_floder,
                output_floder,
                select_upscaler,
                select_upscaler_visibility,
                redraw_amplitude,
            ],
            outputs=[
                id_task,
                task_info,
                process_count,
                process_curr,
            ],
        )

        process_btn.click(
            fn=l.loop_start,
            _js="auLoopStart",
            inputs=[
                id_task,
                process_count,
                process_curr,
            ],
            outputs=[
                out_gallery,
                generation_info,
                html_info,
                html_log,
                id_task,
                process_count,
                process_curr,
            ],
        )

        interrupt.click(
            fn=l.interrupt,
            _js="auInterrupt",
            inputs=[],
            outputs=[
                id_task,
                process_count,
                process_curr,
            ],
        )

    def create_output_panel(tabname):

        with gr.Column(variant='panel', elem_id=f"{tabname}_results"):
            with gr.Group(elem_id=f"{tabname}_gallery_container"):
                result_gallery = gr.Gallery(label='Output', show_label=False, elem_id=f"{tabname}_gallery").style(
                    columns=4)

            generation_info = None
            with gr.Column():
                with gr.Row(elem_id=f"image_buttons_{tabname}", elem_classes="image-buttons"):
                    open_folder_button = gr.Button(folder_symbol, visible=not shared.cmd_opts.hide_ui_dir_config)

                open_folder_button.click(
                    fn=AuUtils.open_folder,
                    inputs=[output_floder],
                    outputs=[],
                )

                if tabname != "extras":

                    with gr.Group():
                        html_info = gr.HTML(elem_id=f'html_info_{tabname}', elem_classes="infotext")
                        html_log = gr.HTML(elem_id=f'html_log_{tabname}', elem_classes="html-log")

                        generation_info = gr.Textbox(visible=False, elem_id=f'generation_info_{tabname}')

                else:
                    html_info_x = gr.HTML(elem_id=f'html_info_x_{tabname}')
                    html_info = gr.HTML(elem_id=f'html_info_{tabname}', elem_classes="infotext")
                    html_log = gr.HTML(elem_id=f'html_log_{tabname}')

                return result_gallery, generation_info if tabname != "extras" else html_info_x, html_info, html_log

    with gr.Blocks(analytics_enabled=False) as ui_component:

        with gr.Row(visible=False):
            id_task = gr.Textbox(visible=True, elem_id=f"{self_type}_id_task", value="")
            task_info = gr.Textbox(visible=True, elem_id=f"{self_type}_task_info", value="")
            process_count = gr.Number(
                visible=True, elem_id=f"{self_type}_process_count", show_label=False, info="总任务数", value=0
            )
            process_curr = gr.Number(
                visible=True, elem_id=f"{self_type}_process_curr", show_label=False, info="当前任务", value=0
            )

        with gr.Row():
            input_floder = gr.Textbox(
                placeholder="待高清修复的图片目录",
                label="输入目录"
            )
        with gr.Row():
            output_floder = gr.Textbox(
                placeholder="",
                label="输出目录"
            )

        with gr.Row():
            with FormRow():
                select_upscaler = gr.Dropdown(
                    label='放大算法', elem_id="select_upscaler", choices=[x.name for x in shared.sd_upscalers],
                    value=shared.sd_upscalers[0].name
                )
                select_upscaler_visibility = gr.Slider(
                    minimum=1.0, maximum=4.0, step=0.5, label="放大倍数", value=1.5,
                    elem_id="select_upscaler_visibility"
                )
                redraw_amplitude = gr.Slider(
                    minimum=0.0, maximum=1.0, step=0.01, label="重绘幅度", value=0.35, elem_id="redraw_amplitude"
                )

        with gr.Row():
            with gr.Column():
                out_gallery, generation_info, html_info, html_log = create_output_panel(self_type)
            with gr.Column(elem_id=f"{self_type}_console"):
                start_btn = gr.Button(
                    value="开始", variant='primary', elem_id=f"{self_type}_start_btn", label='start_btn',
                )
                end_btn = gr.Button(
                    value="终止", variant='secondary', elem_id=f"{self_type}_end_btn", label='end_btn', visible=False
                )
                process_btn = gr.Button(
                    value="处理", variant='secondary', elem_id=f"{self_type}_process_btn", label='process_btn',
                    visible=False
                )

        bind_func(start_btn, end_btn)

        return [(ui_component, "自动高清修复", "auto_upscaler_tab")]


script_callbacks.on_ui_tabs(on_ui_tabs)
