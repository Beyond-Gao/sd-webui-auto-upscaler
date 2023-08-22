import os
import sys
import platform
import subprocess as sp

from modules import shared
from modules.shared import opts


class AuUtils:

    # output_dir = opts.outdir_txt2img_samples

    def init(self):
        pass
        # self.output_dir = opts.outdir_txt2img_samples
    
    # @classmethod
    # def change_output_folder(cls, new_folder):
    #     cls.output_dir = new_folder
    
    @classmethod
    def open_folder(cls, f):
        if f == "":
            f = opts.outdir_txt2img_samples

        if not os.path.exists(f):
            print(f'Folder "{f}" does not exist. After you create an image, the folder will be created.')
            return
        elif not os.path.isdir(f):
            print(f"""
                WARNING
                An open_folder request was made with an argument that is not a folder.
                This could be an error or a malicious attempt to run code on your computer.
                Requested path was: {f}
                """, file=sys.stderr
            )
            return

        if not shared.cmd_opts.hide_ui_dir_config:
            path = os.path.normpath(f)
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                sp.Popen(["open", path])
            elif "microsoft-standard-WSL2" in platform.uname().release:
                sp.Popen(["wsl-open", path])
            else:
                sp.Popen(["xdg-open", path])




