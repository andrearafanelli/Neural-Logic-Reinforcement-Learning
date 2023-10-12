"""
    Reinforcement Learning of an Agent in Procedural Environments
    https://github.com/AAAI-DISIM-UnivAQ/bd-procedural-env-deep-learning
"""

from guizero import App, ListBox, PushButton, Box, Text, info, Slider, CheckBox
from simulator import Environment
from os import listdir
from os.path import isfile, join
from training import Training


class Guizero:
    """A simple and intuitive interface to create graphical user interfaces (GUIs)
    prova"""

    def __init__(self, env_width, env_height, multiplier, fake_collision_mt, door_fake_collision_mt):
        self._env_width = env_width
        self._env_height = env_height
        self._multiplier = multiplier
        self.listbox = None
        self._environment = Environment(env_width, env_height, multiplier, fake_collision_mt,
                                        door_fake_collision_mt)
        self.training = Training(env_width, env_height, multiplier, self._environment)
        self.green = (0, 255, 0)
        self.orange = (255, 200, 140)
        self.pink = (255, 210, 210)
        self.yellow = (255, 255, 150)
        self.light_green = (150, 255, 150)

        self.app = App(title="Procedural Environment Neuro-symbolic Agent", width=800, height=600)
        self.menu_box = Box(self.app, layout="grid", width=800, height=260)
        Box(self.menu_box, height=50, width=800, grid=[0, 0])
        Box(self.menu_box, height=20, width=800, grid=[0, 2])
        Box(self.menu_box, height=20, width=800, grid=[0, 4])
        Box(self.menu_box, height=20, width=800, grid=[0, 6])
        PushButton(self.menu_box, command=self.view_generated_envs, text="Visualize generated environments",
                   width=40,
                   height=1, grid=[0, 1])
        PushButton(self.menu_box, command=self.go_to_sight_generation_cmd, text="Generate new environments", width=30,
                   height=1, grid=[0, 3])
        PushButton(self.menu_box, command=self.train_agent_cmd, text="Train the Agent", width=30, height=1, grid=[0, 5])

        ###GPU###
        PushButton(self.menu_box, command=self.view_gpus, text="Check GPU Availability",
                   width=30,
                   height=1, grid=[0, 7])
        self.gpu_view_box = Box(self.app, visible=False, layout="grid")
        Box(self.gpu_view_box, height=40, width=50, grid=[0, 0])
        gpu_button_box = Box(self.gpu_view_box, height=40, width=300, layout="grid", grid=[0, 2])
        PushButton(gpu_button_box, command=self.view_gpu_back_cmd, text="Back", grid=[1, 0])
        #########

        self.env_view_box = Box(self.app, visible=False, layout="grid")
        Box(self.env_view_box, height=40, width=50, grid=[0, 0])
        view_button_box = Box(self.env_view_box, height=40, width=300, layout="grid", grid=[0, 2])
        PushButton(view_button_box, command=self.view_cmd, text="Visualize", grid=[0, 0])
        PushButton(view_button_box, command=self.view_env_back_cmd, text="Back", grid=[1, 0])

        self.generation_env_box = Box(self.app, visible=False, layout="grid")
        self.generation_env_box1 = Box(self.generation_env_box, visible=False, layout="grid", grid=[0, 1])
        self.generation_env_box2 = Box(self.generation_env_box, visible=False, layout="grid", grid=[1, 1])
        self.generation_env_button = Box(self.generation_env_box, visible=False, layout="grid", grid=[0, 3])

        Box(self.generation_env_box, height=40, width=50, grid=[0, 0])
        Text(self.generation_env_box1, text="Number of bedrooms:", grid=[0, 0], size=10, bg=self.light_green)
        self.sliderBR = Slider(self.generation_env_box1, horizontal=True, end=2, grid=[1, 0])
        self.sliderBR.__setattr__("bg", self.light_green)

        Text(self.generation_env_box2, text="MAX beds:", grid=[0, 0], size=10, bg=self.light_green)
        self.sliderBR_B = Slider(self.generation_env_box2, horizontal=True, end=2, grid=[1, 0])
        Text(self.generation_env_box2, text="MAX cabinets:", grid=[0, 1], size=10, bg=self.light_green)
        self.sliderBR_W = Slider(self.generation_env_box2, horizontal=True, end=2, grid=[1, 1])

        Box(self.generation_env_box1, height=40, width=50, grid=[0, 1])

        Text(self.generation_env_box1, text="Number of bathrooms:", grid=[0, 2], size=10, bg=self.pink)
        self.sliderBAR = Slider(self.generation_env_box1, horizontal=True, end=2, grid=[1, 2])
        self.sliderBAR.__setattr__("bg", self.pink)
        Text(self.generation_env_box2, text="MAX water:", grid=[0, 2], size=10, bg=self.pink)
        self.sliderBAR_T = Slider(self.generation_env_box2, horizontal=True, end=1, grid=[1, 2])
        Text(self.generation_env_box2, text="MAX showers:", grid=[0, 3], size=10, bg=self.pink)
        self.sliderBAR_S = Slider(self.generation_env_box2, horizontal=True, end=1, grid=[1, 3])
        Text(self.generation_env_box2, text="MAX sinks:", grid=[0, 4], size=10, bg=self.pink)
        self.sliderBAR_SI = Slider(self.generation_env_box2, horizontal=True, end=1, grid=[1, 4])

        Box(self.generation_env_box1, height=40, width=50, grid=[0, 3])

        Text(self.generation_env_box1, text="Number of kitchens:", grid=[0, 4], size=10, bg=self.yellow)
        self.sliderKI = Slider(self.generation_env_box1, horizontal=True, end=2, grid=[1, 4])
        self.sliderKI.__setattr__("bg", self.yellow)

        Text(self.generation_env_box2, text="MAX tables:", grid=[0, 5], size=10, bg=self.yellow)
        self.sliderKI_KTA = Slider(self.generation_env_box2, horizontal=True, end=1, grid=[1, 5])
        Text(self.generation_env_box2, text="MAX balconies:", grid=[0, 6], size=10, bg=self.yellow)
        self.sliderKI_D = Slider(self.generation_env_box2, horizontal=True, end=3, grid=[1, 6])

        Box(self.generation_env_box1, height=40, width=50, grid=[0, 5])

        Text(self.generation_env_box1, text="Number of halls:", grid=[0, 6], size=10, bg=self.orange)
        self.sliderHA = Slider(self.generation_env_box1, horizontal=True, start=1, end=1, grid=[1, 6])
        self.sliderHA.__setattr__("bg", self.orange)

        Text(self.generation_env_box2, text="MAX tables:", grid=[0, 7], size=10, bg=self.orange)
        self.sliderHA_HT = Slider(self.generation_env_box2, horizontal=True, end=1, grid=[1, 7])
        Text(self.generation_env_box2, text="MAX sofa:", grid=[0, 8], size=10, bg=self.orange)
        self.sliderHA_SO = Slider(self.generation_env_box2, horizontal=True, end=2, grid=[1, 8])
        Text(self.generation_env_box2, text="MAX shelves:", grid=[0, 9], size=10, bg=self.orange)
        self.sliderHA_CB = Slider(self.generation_env_box2, horizontal=True, end=2, grid=[1, 9])

        Box(self.generation_env_box, height=40, width=50, grid=[0, 2])

        PushButton(self.generation_env_button, command=self.generate_cmd, text="Generate Environments", grid=[0, 0])
        PushButton(self.generation_env_button, command=self.view_generation_back_cmd, text="Back", grid=[1, 0])

        self.train_box_view = Box(self.app, visible=False, layout="grid")
        env_files = [f for f in listdir("./environments") if isfile(join("./environments", f)) and f != "null"]
        env_files = sorted(env_files)
        self.listbox2 = ListBox(self.train_box_view, items=env_files, scrollbar=True, width=350, height=350,
                                grid=[0, 1])
        self.render_on = CheckBox(self.train_box_view, text="Render On", grid=[0, 3])
        self.render_on.toggle()
        self.logic_drive_on = CheckBox(self.train_box_view, text="Logic Drive On", grid=[0, 4])
        self.video_rec_on = CheckBox(self.train_box_view, text="Video REC On", grid=[0, 5])
        Box(self.train_box_view, height=40, width=50, grid=[0, 0])
        view_button_box2 = Box(self.train_box_view, layout="grid", grid=[0, 2])
        PushButton(view_button_box2, command=self.train_cmd, text="Train", grid=[0, 0])
        PushButton(view_button_box2, command=self.view_train_back_cmd, text="Back", grid=[1, 0])

        self.app.display()

    def update_files(self):
        env_files = [f for f in listdir("./environments") if isfile(join("./environments", f)) and f != "null"]
        env_files = sorted(env_files)
        self.listbox = ListBox(self.env_view_box, items=env_files, scrollbar=True, width=350, height=350, grid=[0, 1])
        self.listbox2 = ListBox(self.train_box_view, items=env_files, scrollbar=True, width=350, height=350,
                                grid=[0, 1])

    def view_generated_envs(self):
        self.update_files()
        self.menu_box.hide()
        self.env_view_box.show()

    def go_to_sight_generation_cmd(self):
        self.menu_box.hide()
        self.generation_env_box.show()
        self.generation_env_box1.show()
        self.generation_env_box2.show()
        self.generation_env_button.show()

    def train_agent_cmd(self):
        self.update_files()
        self.menu_box.hide()
        self.train_box_view.show()

    def view_cmd(self):
        self.training.load_model(self.listbox.value, self.render_on.value)
        self.training._env_width = self._env_width
        self.training._env_height = self._env_height
        self.training._multiplier = self._multiplier
        self._environment._rooms = self.training._rooms
        self._environment._agent = self.training._agent
        self._environment._objective = self.training._objective
        self._environment._floor = self.training._floor
        self._environment._screen = self.training._screen
        self._environment._env_width = self._env_width
        self._environment._env_height = self._env_height
        self._environment._multiplier = self._multiplier

        # self._environment.draw_model()
        self._environment.display_environment(self.sliderBAR.value, self.sliderBR.value, self.sliderKI.value,
                                              self.sliderHA.value)

    def view_env_back_cmd(self):
        self.env_view_box.hide()
        self.menu_box.show()

    def view_generation_back_cmd(self):
        self.generation_env_box.hide()
        self.generation_env_box1.hide()
        self.generation_env_box2.hide()
        self.generation_env_button.hide()
        self.menu_box.show()

    def generate_cmd(self):
        info("Use the Generator",
             "- During the environments generation, press key 'S' to save an _environment and generate the next."
             "\n\n- Press key 'N' to generate a new _environment discarding the previous."
             "\n\n- Close PyGame to comeback to the menu.")
        self._environment.generate_environment(self.sliderBAR.value, self.sliderBR.value, self.sliderKI.value,
                                               self.sliderHA.value)
        self._environment.draw_model()
        self._environment.display_environment(self.sliderBAR.value, self.sliderBR.value, self.sliderKI.value,
                                              self.sliderHA.value, mode="generate")

    def train_cmd(self):
        self.training.load_model(self.listbox2.value, self.render_on.value)
        self.training.run_training(bool(self.render_on.value), bool(self.video_rec_on.value), bool(self.logic_drive_on.value))

    def view_train_back_cmd(self):
        self.train_box_view.hide()
        self.menu_box.show()

    ###GPU###
    def view_gpus(self):
        try:
            import tensorflow as tf
            gpus = [f"{tf.config.experimental.get_device_details(gpu).get('device_name', 'unknown')} {gpu.name}"
                    for gpu in tf.config.list_physical_devices('GPU')]
        except:
            gpus = []
        self.listbox_gpu = ListBox(self.gpu_view_box, items=gpus, scrollbar=True, width=350, height=350, grid=[0, 1])
        self.menu_box.hide()
        self.gpu_view_box.show()

    #########
    ###GPU###
    def view_gpu_back_cmd(self):
        self.gpu_view_box.hide()
        self.menu_box.show()
    #########


if __name__ == "__main__":
    Guizero(15.0, 15.0, 8.5, 2.5, 1.5)
