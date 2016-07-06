# Conditional import machinery for vtk.
from dipy.utils.optpkg import optional_package

from ipdb import set_trace

# Allow import, but disable doctests if we don't have vtk.
vtk, have_vtk, setup_module = optional_package('vtk')

if have_vtk:
    vtkInteractorStyleUser = vtk.vtkInteractorStyleUser
    version = vtk.vtkVersion.GetVTKSourceVersion().split(' ')[-1]
    major_version = vtk.vtkVersion.GetVTKMajorVersion()
else:
    vtkInteractorStyleUser = object

numpy_support, have_ns, _ = optional_package('vtk.util.numpy_support')


class UI(object):
    def __init__(self):
        self.ui_param = None
        self.ui_list = list()

    def set_ui_param(self, ui_param):
        self.ui_param = ui_param


class Button(UI):
    """ Currently implements a 2D overlay button and is of type vtkTexturedActor2D.

    """

    def __init__(self, icon_fnames):
        super(Button, self).__init__()
        self.icons = self.build_icons(icon_fnames)
        self.icon_names = list(self.icons.keys())
        self.current_icon_id = 0
        self.current_icon_name = self.icon_names[self.current_icon_id]
        self.actor = self.build_actor(self.icons[self.current_icon_name])

        self.ui_list.append(self)

    def build_icons(self, icon_fnames):
        """ Converts filenames to vtkImageDataGeometryFilters
        A peprocessing step to prevent re-read of filenames during every state change

        Parameters
        ----------
        icon_fnames : A list of filenames

        Returns
        -------
        icons : A list of corresponding vtkImageDataGeometryFilters
        """
        icons = {}
        for icon_name, icon_fname in icon_fnames.items():
            png = vtk.vtkPNGReader()
            png.SetFileName(icon_fname)
            png.Update()

            # Convert the image to a polydata
            imageDataGeometryFilter = vtk.vtkImageDataGeometryFilter()
            imageDataGeometryFilter.SetInputConnection(png.GetOutputPort())
            imageDataGeometryFilter.Update()

            icons[icon_name] = imageDataGeometryFilter

        return icons

    def build_actor(self, icon, center=None):
        """ Return an image as a 2D actor with a specific position

        Parameters
        ----------
        icon : imageDataGeometryFilter
        position : a two tuple
        center : a two tuple

        Returns
        -------
        button : vtkTexturedActor2D
        """

        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInputConnection(icon.GetOutputPort())

        button = vtk.vtkTexturedActor2D()
        button.SetMapper(mapper)

        if center is not None:
            button.SetCenter(*center)

        return button

    def add_callback(self, event_type, callback):
        """ Adds events to button actor

        Parameters
        ----------
        event_type: event code
        callback: callback function
        """
        self.actor.AddObserver(event_type, callback)

    def set_icon(self, icon):
        """ Modifies the icon used by the vtkTexturedActor2D

        Parameters
        ----------
        icon : imageDataGeometryFilter
        """
        self.actor.GetMapper().SetInputConnection(icon.GetOutputPort())

    def next_icon_name(self):
        self.current_icon_id += 1
        if self.current_icon_id == len(self.icons):
            self.current_icon_id = 0
        self.current_icon_name = self.icon_names[self.current_icon_id]

    def next_icon(self):
        """ Increments the state of the Button
            Also changes the icon
        """
        self.next_icon_name()
        self.set_icon(self.icons[self.current_icon_name])


class TextActor(vtk.vtkTextActor):
    def message(self, text):
        self.SetInput(text)

    def set_message(self, text):
        self.SetInput(text)

    def get_message(self):
        return self.GetInput()

    def font_size(self, size):
        self.GetTextProperty().SetFontSize(size)

    def font_family(self, family='Arial'):
        self.GetTextProperty().SetFontFamilyToArial()

    def justification(self, justification):
        tprop = self.GetTextProperty()
        if justification == 'left':
            tprop.SetJustificationToLeft()
        if justification == 'center':
            tprop.SetJustificationToCentered()
        if justification == 'right':
            tprop.SetJustificationToRight()

    def font_style(self, bold=False, italic=False, shadow=False):
        tprop = self.GetTextProperty()
        if bold:
            tprop.BoldOn()
        else:
            tprop.BoldOff()
        if italic:
            tprop.ItalicOn()
        else:
            tprop.ItalicOff()
        if shadow:
            tprop.ShadowOn()
        else:
            tprop.ShadowOff()

    def color(self, color):
        self.GetTextProperty().SetColor(*color)

    def set_position(self, position):
        self.SetDisplayPosition(*position)

    def get_position(self):
        return self.GetDisplayPosition()


class TextBox(UI):
    def __init__(self, width, height, text="Enter Text"):
        """

        Parameters
        ----------
        width
        height
        text
        """
        super(TextBox, self).__init__()
        self.text = text
        self.actor = self.build_actor(self.text)
        self.width = width
        self.height = height
        self.window_left = 0
        self.window_right = 0
        self.caret_pos = 0
        self.init = True

        self.ui_list.append(self)

    def build_actor(self, text, position=(100, 10), color=(1, 1, 1),
                    font_size=18, font_family='Arial', justification='left',
                    bold=False, italic=False, shadow=False):

        """ Builds a text actor

        Parameters
        ----------
        text
        position
        color
        font_size
        font_family
        justification
        bold
        italic
        shadow

        Returns
        -------
        text_actor

        """
        text_actor = TextActor()
        text_actor.set_position(position)
        text_actor.message(text)
        text_actor.font_size(font_size)
        text_actor.font_family(font_family)
        text_actor.justification(justification)
        text_actor.font_style(bold, italic, shadow)
        text_actor.color(color)

        return text_actor

    def add_callback(self, event_type, callback):
        """ Adds events to the text actor

        Parameters
        ----------
        event_type: event code
        callback: callback function
        """
        self.actor.AddObserver(event_type, callback)

    def width_set_text(self, text):
        """ Adds newlines to text where necessary

        Parameters
        ----------
        text

        Returns
        -------
        multi_line_text

        """
        multi_line_text = ""
        for i in range(len(text)):
            multi_line_text += text[i]
            if (i + 1) % self.width == 0:
                multi_line_text += "\n"
        return multi_line_text.rstrip("\n")

    def handle_character(self, character):
        """ Main driving function that handles button events

        Parameters
        ----------
        character
        """
        if character.lower() == "return":
            self.render_text(False)
        else:
            if character.lower() == "backspace":
                self.remove_character()
            elif character.lower() == "left":
                self.move_left()
            elif character.lower() == "right":
                self.move_right()
            else:
                self.add_character(character)
            self.render_text()

    def move_caret_right(self):
        """ Moves the caret towards right

        """
        self.caret_pos += 1
        if self.caret_pos > len(self.text):
            self.caret_pos = len(self.text)

    def move_caret_left(self):
        """ Moves the caret towards left

        """
        self.caret_pos -= 1
        if self.caret_pos < 0:
            self.caret_pos = 0

    def right_move_right(self):
        """ Moves right window right

        """
        if self.window_right <= len(self.text):
            self.window_right += 1

    def right_move_left(self):
        """ Moves right window left

        """
        if self.window_right > 0:
            self.window_right -= 1

    def left_move_right(self):
        """ Moves left window right

        """
        if self.window_left <= len(self.text):
            self.window_left += 1

    def left_move_left(self):
        """ Moves left window left

        """
        if self.window_left > 0:
            self.window_left -= 1

    def add_character(self, character):
        """ Inserts a character into the text and moves window and caret accordingly

        Parameters
        ----------
        character

        Returns
        -------

        """
        if len(character) > 1 and character.lower() != "space":
            return
        if character.lower() == "space":
            character = " "
        self.text = self.text[:self.caret_pos] + character + self.text[self.caret_pos:]
        self.move_caret_right()
        if self.window_right - self.window_left == self.height * self.width - 1:
            self.left_move_right()
        self.right_move_right()

    def remove_character(self):
        """ Removes a character from the text and moves window and caret accordingly

        Returns
        -------

        """
        if self.caret_pos == 0:
            return
        self.text = self.text[:self.caret_pos - 1] + self.text[self.caret_pos:]
        self.move_caret_left()
        if len(self.text) < self.height * self.width - 1:
            self.right_move_left()
        if self.window_right - self.window_left == self.height * self.width - 1:
            if self.window_left > 0:
                self.left_move_left()
                self.right_move_left()

    def move_left(self):
        """ Handles left button press

        """
        self.move_caret_left()
        if self.caret_pos == self.window_left - 1:
            if self.window_right - self.window_left == self.height * self.width - 1:
                self.left_move_left()
                self.right_move_left()

    def move_right(self):
        """ Handles right button press

        """
        self.move_caret_right()
        if self.caret_pos == self.window_right + 1:
            if self.window_right - self.window_left == self.height * self.width - 1:
                self.left_move_right()
                self.right_move_right()

    def showable_text(self, show_caret):
        """ Chops out text to be shown on the screen

        Parameters
        ----------
        show_caret

        Returns
        -------

        """
        if show_caret:
            ret_text = self.text[:self.caret_pos] + "_" + self.text[self.caret_pos:]
        else:
            ret_text = self.text
        ret_text = ret_text[self.window_left:self.window_right + 1]
        return ret_text

    def render_text(self, show_caret=True):
        """ Renders text

        Parameters
        ----------
        show_caret
        """
        text = self.showable_text(show_caret)
        if text == "":
            text = "Enter Text"
        self.actor.set_message(self.width_set_text(text))

    def edit_mode(self):
        """ Turns on edit mode

        """
        if self.init:
            self.text = ""
            self.init = False
            self.caret_pos = 0
        self.render_text()


class Slider(UI):
    def __init__(self, start_point=(350, 20), end_point=(550, 20), line_width=5, inner_radius=5,
                 outer_radius=15, position=(450, 20)):
        """

        Parameters
        ----------
        inner_radius
        outer_radius
        position
        start_point
        end_point
        line_width
        """
        super(Slider, self).__init__()
        self.slider_line = SliderLine(start_point=start_point, end_point=end_point, line_width=line_width)
        self.slider_disk = SliderDisk(position=position, inner_radius=inner_radius, outer_radius=outer_radius,
                                      start_point=start_point, end_point=end_point)
        self.text = SliderText(limits=(start_point, end_point),
                               current_val=(start_point[0] + (end_point[0] - start_point[0])/2),
                               position=(start_point[0]-40, start_point[1]-10))

        self.ui_list.append(self.slider_disk)
        self.ui_list.append(self.slider_line)
        self.ui_list.append(self.text)

    def add_callback(self, event_type, callback, component):
        """ Adds events to an actor

        Parameters
        ----------
        event_type: event code
        callback: callback function
        component: component
        """
        component.actor.AddObserver(event_type, callback)


class SliderLine(UI):

    def __init__(self, start_point, end_point, line_width):
        """

        Parameters
        ----------
        start_point
        end_point
        line_width
        """
        super(SliderLine, self).__init__()
        self.start_point = start_point
        self.end_point = end_point
        self.actor = self.build_actor(start_point=start_point, end_point=end_point, line_width=line_width)

        self.ui_list.append(self)

    def build_actor(self, start_point, end_point, line_width):
        """

        Parameters
        ----------
        start_point
        end_point
        line_width

        Returns
        -------
        actor

        """
        line = vtk.vtkLineSource()
        line.SetPoint1(start_point[0], start_point[1], 0)
        line.SetPoint2(end_point[0], end_point[1], 0)

        # mapper
        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInputConnection(line.GetOutputPort())

        # actor
        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)

        actor.GetProperty().SetLineWidth(line_width)

        return actor

    def add_callback(self, event_type, callback):
        """ Adds events to the actor

        Parameters
        ----------
        event_type: event code
        callback: callback function
        """
        self.actor.AddObserver(event_type, callback)


class SliderDisk(UI):

    def __init__(self, position, inner_radius, outer_radius, start_point, end_point):
        """

        Parameters
        ----------
        position
        inner_radius
        outer_radius
        """
        super(SliderDisk, self).__init__()
        self.actor = self.build_actor(position=position, inner_radius=inner_radius, outer_radius=outer_radius)
        self.pos_height = position[1]

        self.start_point = start_point
        self.end_point = end_point

        self.ui_list.append(self)

    def build_actor(self, position, inner_radius, outer_radius):
        # create source
        """

        Parameters
        ----------
        position
        inner_radius
        outer_radius

        Returns
        -------
        actor

        """
        disk = vtk.vtkDiskSource()
        disk.SetInnerRadius(inner_radius)
        disk.SetOuterRadius(outer_radius)
        disk.SetRadialResolution(100)
        disk.SetCircumferentialResolution(100)
        disk.Update()

        # mapper
        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInputConnection(disk.GetOutputPort())

        # actor
        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)

        actor.SetPosition(position[0], position[1])

        return actor

    def set_position(self, position):
        """ Sets the disk's position

        Parameters
        ----------
        position
        """
        x_position = position[0]
        if x_position < self.start_point[0]:
            x_position = self.start_point[0]
        if x_position > self.end_point[0]:
            x_position = self.end_point[0]
        self.actor.SetPosition(x_position, self.pos_height)

    def add_callback(self, event_type, callback):
        """ Adds events to the actor

        Parameters
        ----------
        event_type: event code
        callback: callback function
        """
        self.actor.AddObserver(event_type, callback)


class SliderText(UI):

    def __init__(self, limits, current_val, position):
        super(SliderText, self).__init__()
        self.y_position = (limits[0][1] + limits[1][1])/2
        self.left_x_position = limits[0][0]
        self.right_x_position = limits[1][0]

        self.actor = self.build_actor(current_val=current_val, position=position)

        self.ui_list.append(self)

    def calculate_percentage(self, current_val):
        percentage = ((current_val-self.left_x_position)*100)/(self.right_x_position-self.left_x_position)
        if percentage < 0:
            percentage = 0
        if percentage > 100:
            percentage = 100
        return str(percentage) + "%"

    def build_actor(self, current_val, position):
        """

        Parameters
        ----------
        current_val
        position

        Returns
        -------
        actor

        """
        actor = TextActor()

        actor.set_position(position=position)
        percentage = self.calculate_percentage(current_val=current_val)
        actor.set_message(text=percentage)
        actor.font_size(size=16)

        return actor

    def set_percentage(self, current_val):
        percentage = self.calculate_percentage(current_val=current_val)
        self.actor.set_message(text=percentage)