from __future__ import division
from _warnings import warn

import os
import glob
import numpy as np

from dipy.data import read_viz_icons
from dipy.viz.interactor import CustomInteractorStyle

from dipy.utils.optpkg import optional_package

# Allow import, but disable doctests if we don't have vtk.
vtk, have_vtk, setup_module = optional_package('vtk')

if have_vtk:
    version = vtk.vtkVersion.GetVTKVersion()
    major_version = vtk.vtkVersion.GetVTKMajorVersion()

TWO_PI = 2 * np.pi


class UI(object):
    """ An umbrella class for all UI elements.

    While adding UI elements to the renderer, we go over all the sub-elements
    that come with it and add those to the renderer automatically.

    Attributes
    ----------
    position : (float, float)
        Absolute coordinates (x, y) in pixels the lower-left corner.
    size : (float, float)
        Size (width, height) in pixels of this UI component.
    on_left_mouse_button_pressed: function
        Callback function for when the left mouse button is pressed.
    on_left_mouse_button_released: function
        Callback function for when the left mouse button is released.
    on_left_mouse_button_clicked: function
        Callback function for when clicked using the left mouse button
        (i.e. pressed -> released).
    on_left_mouse_button_dragged: function
        Callback function for when dragging using the left mouse button.
    on_right_mouse_button_pressed: function
        Callback function for when the right mouse button is pressed.
    on_right_mouse_button_released: function
        Callback function for when the right mouse button is released.
    on_right_mouse_button_clicked: function
        Callback function for when clicking using the right mouse button
        (i.e. pressed -> released).
    on_right_mouse_button_dragged: function
        Callback function for when dragging using the right mouse button.

    """

    def __init__(self):
        """
        Parameters
        ----------
        size : (int, int)
            Size (width, height) in pixels of this UI component.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of this
            UI component.
        """
        self._callbacks = []

        self.left_button_state = "released"
        self.right_button_state = "released"

        self.on_left_mouse_button_pressed = lambda i_ren, obj, element: None
        self.on_left_mouse_button_dragged = lambda i_ren, obj, element: None
        self.on_left_mouse_button_released = lambda i_ren, obj, element: None
        self.on_left_mouse_button_clicked = lambda i_ren, obj, element: None
        self.on_right_mouse_button_pressed = lambda i_ren, obj, element: None
        self.on_right_mouse_button_released = lambda i_ren, obj, element: None
        self.on_right_mouse_button_clicked = lambda i_ren, obj, element: None
        self.on_right_mouse_button_dragged = lambda i_ren, obj, element: None
        self.on_key_press = lambda i_ren, obj, element: None

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        msg = "Subclasses of UI must implement `get_actors(self)`."
        raise NotImplementedError(msg)

    def add_to_renderer(self, ren):
        """ Allows UI objects to add their own props to the renderer.

        Parameters
        ----------
        ren : renderer

        """
        ren.add(*self.get_actors())

        # Get a hold on the current interactor style.
        iren = ren.GetRenderWindow().GetInteractor().GetInteractorStyle()

        for callback in self._callbacks:
            if not isinstance(iren, CustomInteractorStyle):
                msg = ("The ShowManager requires `CustomInteractorStyle` in"
                       " order to use callbacks.")
                raise TypeError(msg)

            iren.add_callback(*callback, args=[self])

    def add_callback(self, prop, event_type, callback, priority=0):
        """ Adds a callback to a specific event for this UI component.

        Parameters
        ----------
        prop : vtkProp
            The prop on which is callback is to be added.
        event_type : string
            The event code.
        callback : function
            The callback function.
        priority : int
            Higher number is higher priority.

        """
        # Actually since we need an interactor style we will add the callback
        # only when this UI component is added to the renderer.
        self._callbacks.append((prop, event_type, callback, priority))

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, coords):
        self._set_position(coords)
        self._position = coords

    def _set_position(self, coords):
        """ Position the lower-left corner of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        msg = "Subclasses of UI must implement `_set_position(self, coords)`."
        raise NotImplementedError(msg)

    def set_center(self, coords):
        """ Position the center of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        if not hasattr(self, "size"):
            msg = "Subclasses of UI must implement the `size` property."
            raise NotImplementedError(msg)

        new_center = np.array(coords)
        size = np.array(self.size)
        new_lower_left_corner = new_center - size / 2.
        self.position = new_lower_left_corner

    def set_visibility(self, visibility):
        """ Sets visibility of this UI component and all its sub-components.

        """
        for actor in self.get_actors():
            actor.SetVisibility(visibility)

    def handle_events(self, actor):
        self.add_callback(actor, "LeftButtonPressEvent", self.left_button_click_callback)
        self.add_callback(actor, "LeftButtonReleaseEvent", self.left_button_release_callback)
        self.add_callback(actor, "RightButtonPressEvent", self.right_button_click_callback)
        self.add_callback(actor, "RightButtonReleaseEvent", self.right_button_release_callback)
        self.add_callback(actor, "MouseMoveEvent", self.mouse_move_callback)
        self.add_callback(actor, "KeyPressEvent", self.key_press_callback)

    @staticmethod
    def left_button_click_callback(i_ren, obj, self):
        self.left_button_state = "pressing"
        self.on_left_mouse_button_pressed(i_ren, obj, self)
        i_ren.event.abort()

    @staticmethod
    def left_button_release_callback(i_ren, obj, self):
        if self.left_button_state == "pressing":
            self.on_left_mouse_button_clicked(i_ren, obj, self)
        self.left_button_state = "released"
        self.on_left_mouse_button_released(i_ren, obj, self)

    @staticmethod
    def right_button_click_callback(i_ren, obj, self):
        self.right_button_state = "pressing"
        self.on_right_mouse_button_pressed(i_ren, obj, self)
        i_ren.event.abort()

    @staticmethod
    def right_button_release_callback(i_ren, obj, self):
        if self.right_button_state == "pressing":
            self.on_right_mouse_button_clicked(i_ren, obj, self)
        self.right_button_state = "released"
        self.on_right_mouse_button_released(i_ren, obj, self)

    @staticmethod
    def mouse_move_callback(i_ren, obj, self):
        if self.left_button_state == "pressing" or self.left_button_state == "dragging":
            self.left_button_state = "dragging"
            self.on_left_mouse_button_dragged(i_ren, obj, self)
        elif self.right_button_state == "pressing" or self.right_button_state == "dragging":
            self.right_button_state = "dragging"
            self.on_right_mouse_button_dragged(i_ren, obj, self)
        else:
            pass

    @staticmethod
    def key_press_callback(i_ren, obj, self):
        self.on_key_press(i_ren, obj, self)


class Button2D(UI):
    """ A 2D overlay button and is of type vtkTexturedActor2D.
    Currently supports:
    - Multiple icons.
    - Switching between icons.

    Attributes
    ----------
    size: (float, float)
        Button size (width, height) in pixels.

    """

    def __init__(self, icon_fnames, size=(30, 30)):
        """
        Parameters
        ----------
        size : (int, int)
            Size (width, height) in pixels of the button.
        icon_fnames : dict
            {iconname : filename, iconname : filename, ...}

        """
        super(Button2D, self).__init__()
        self.icon_extents = dict()
        self.icons = self.__build_icons(icon_fnames)
        self.icon_names = list(self.icons.keys())
        self.current_icon_id = 0
        self.current_icon_name = self.icon_names[self.current_icon_id]
        self.actor = self.build_actor(self.icons[self.current_icon_name])
        self.size = size
        self.handle_events(self.actor)

    def __build_icons(self, icon_fnames):
        """ Converts file names to vtkImageDataGeometryFilters.

        A pre-processing step to prevent re-read of file names during every
        state change.

        Parameters
        ----------
        icon_fnames : dict
            {iconname: filename, iconname: filename, ...}

        Returns
        -------
        icons : dict
            A dictionary of corresponding vtkImageDataGeometryFilters.

        """
        icons = {}
        for icon_name, icon_fname in icon_fnames.items():
            if icon_fname.split(".")[-1] not in ["png", "PNG"]:
                error_msg = "A specified icon file is not in the PNG format. SKIPPING."
                warn(Warning(error_msg))
            else:
                png = vtk.vtkPNGReader()
                png.SetFileName(icon_fname)
                png.Update()
                icons[icon_name] = png.GetOutput()

        return icons

    @property
    def size(self):
        """ Gets the button size.

        """
        return self._size

    @size.setter
    def size(self, size):
        """ Sets the button size.

        Parameters
        ----------
        size : (float, float)
            Button size (width, height) in pixels.

        """
        self._size = np.asarray(size)

        # Update actor.
        self.texture_points.SetPoint(0, 0, 0, 0.0)
        self.texture_points.SetPoint(1, size[0], 0, 0.0)
        self.texture_points.SetPoint(2, size[0], size[1], 0.0)
        self.texture_points.SetPoint(3, 0, size[1], 0.0)
        self.texture_polydata.SetPoints(self.texture_points)

    @property
    def color(self):
        """ Gets the button's color.

        """
        color = self.actor.GetProperty().GetColor()
        return np.asarray(color)

    @color.setter
    def color(self, color):
        """ Sets the button's color.

        Parameters
        ----------
        color : (float, float, float)
            RGB. Must take values in [0, 1].

        """
        self.actor.GetProperty().SetColor(*color)

    def scale(self, size):
        """ Scales the button.

        Parameters
        ----------
        size : (float, float)
            Scaling factor (width, height) in pixels.

        """
        self.size *= size

    def build_actor(self, icon):
        """ Return an image as a 2D actor with a specific position.

        Parameters
        ----------
        icon : :class:`vtkImageData`

        Returns
        -------
        :class:`vtkTexturedActor2D`

        """
        # This is highly inspired by
        # https://github.com/Kitware/VTK/blob/c3ec2495b183e3327820e927af7f8f90d34c3474\
        # /Interaction/Widgets/vtkBalloonRepresentation.cxx#L47

        self.texture_polydata = vtk.vtkPolyData()
        self.texture_points = vtk.vtkPoints()
        self.texture_points.SetNumberOfPoints(4)
        self.size = icon.GetExtent()

        polys = vtk.vtkCellArray()
        polys.InsertNextCell(4)
        polys.InsertCellPoint(0)
        polys.InsertCellPoint(1)
        polys.InsertCellPoint(2)
        polys.InsertCellPoint(3)
        self.texture_polydata.SetPolys(polys)

        tc = vtk.vtkFloatArray()
        tc.SetNumberOfComponents(2)
        tc.SetNumberOfTuples(4)
        tc.InsertComponent(0, 0, 0.0)
        tc.InsertComponent(0, 1, 0.0)
        tc.InsertComponent(1, 0, 1.0)
        tc.InsertComponent(1, 1, 0.0)
        tc.InsertComponent(2, 0, 1.0)
        tc.InsertComponent(2, 1, 1.0)
        tc.InsertComponent(3, 0, 0.0)
        tc.InsertComponent(3, 1, 1.0)
        self.texture_polydata.GetPointData().SetTCoords(tc)

        texture_mapper = vtk.vtkPolyDataMapper2D()
        if major_version <= 5:
            texture_mapper.SetInput(self.texture_polydata)
        else:
            texture_mapper.SetInputData(self.texture_polydata)

        button = vtk.vtkTexturedActor2D()
        button.SetMapper(texture_mapper)

        self.texture = vtk.vtkTexture()
        button.SetTexture(self.texture)

        button_property = vtk.vtkProperty2D()
        button_property.SetOpacity(1.0)
        button.SetProperty(button_property)

        self.set_icon(icon)
        return button

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        return [self.actor]

    def set_icon(self, icon):
        """ Modifies the icon used by the vtkTexturedActor2D.

        Parameters
        ----------
        icon : imageDataGeometryFilter

        """
        if major_version <= 5:
            self.texture.SetInput(icon)
        else:
            self.texture.SetInputData(icon)

    def next_icon_name(self):
        """ Returns the next icon name while cycling through icons.

        """
        self.current_icon_id += 1
        if self.current_icon_id == len(self.icons):
            self.current_icon_id = 0
        self.current_icon_name = self.icon_names[self.current_icon_id]

    def next_icon(self):
        """ Increments the state of the Button.

            Also changes the icon.

        """
        self.next_icon_name()
        self.set_icon(self.icons[self.current_icon_name])

    def _set_position(self, coords):
        """ Position the lower-left corner of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        self.actor.SetPosition(*coords)


class Rectangle2D(UI):
    """ A 2D rectangle sub-classed from UI.
    Uses vtkPolygon.

    Attributes
    ----------
    size : (float, float)
        The size of the rectangle (height, width) in pixels.

    """

    def __init__(self, size, position=(0, 0), color=(1, 1, 1), opacity=1.0):
        """ Initializes a rectangle.

        Parameters
        ----------
        size : (int, int)
            The size of the rectangle (height, width) in pixels.
        position : (float, float)
            Coordinates (x, y) of the lower-left corner of the rectangle.
        color : (float, float, float)
            Must take values in [0, 1].
        opacity : float
            Must take values in [0, 1].

        """
        super(Rectangle2D, self).__init__()
        self.size = size
        self.actor = self.build_actor()
        self.color = color
        self.opacity = opacity
        self.handle_events(self.actor)
        self.position = position

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        return [self.actor]

    def build_actor(self):
        """ Builds the text actor.

        Returns
        -------
        :class:`vtkActor2D`

        """
        # Setup four points
        points = vtk.vtkPoints()
        points.InsertNextPoint(0, 0, 0)
        points.InsertNextPoint(self.size[0], 0, 0)
        points.InsertNextPoint(self.size[0], self.size[1], 0)
        points.InsertNextPoint(0, self.size[1], 0)

        # Create the polygon
        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(4)  # make a quad
        polygon.GetPointIds().SetId(0, 0)
        polygon.GetPointIds().SetId(1, 1)
        polygon.GetPointIds().SetId(2, 2)
        polygon.GetPointIds().SetId(3, 3)

        # Add the polygon to a list of polygons
        polygons = vtk.vtkCellArray()
        polygons.InsertNextCell(polygon)

        # Create a PolyData
        polygonPolyData = vtk.vtkPolyData()
        polygonPolyData.SetPoints(points)
        polygonPolyData.SetPolys(polygons)

        # Create a mapper and actor
        mapper = vtk.vtkPolyDataMapper2D()
        if vtk.VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(polygonPolyData)
        else:
            mapper.SetInputData(polygonPolyData)

        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)

        return actor

    def _set_position(self, coords):
        """ Position the lower-left corner of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        self.actor.SetPosition(*coords)

    @property
    def color(self):
        """ Gets the rectangle's color.

        """
        color = self.actor.GetProperty().GetColor()
        return np.asarray(color)

    @color.setter
    def color(self, color):
        """ Sets the rectangle's color.

        Parameters
        ----------
        color : (float, float, float)
            RGB. Must take values in [0, 1].

        """
        self.actor.GetProperty().SetColor(*color)

    @property
    def opacity(self):
        """ Gets the rectangle's opacity.

        """
        return self.actor.GetProperty().GetOpacity()

    @opacity.setter
    def opacity(self, opacity):
        """ Sets the rectangle's opacity.

        Parameters
        ----------
        opacity : float
            Degree of transparency. Must be between [0, 1].

        """
        self.actor.GetProperty().SetOpacity(opacity)


class Panel2D(UI):
    """ A 2D UI Panel.

    Can contain one or more UI elements.

    Attributes
    ----------
    alignment : [left, right]
        Alignment of the panel with respect to the overall screen.

    """

    def __init__(self, size, position=(0, 0), color=(0.1, 0.1, 0.1),
                 opacity=0.7, align="left"):
        """
        Parameters
        ----------
        size : (int, int)
            Size (width, height) in pixels of the panel.
        position : (float, float)
            Absolute coordinates (x, y) of the lower-left corner of the panel.
        color : (float, float, float)
            Must take values in [0, 1].
        opacity : float
            Must take values in [0, 1].
        align : [left, right]
            Alignment of the panel with respect to the overall screen.

        """
        super(Panel2D, self).__init__()
        self._elements = []
        self.element_positions = []

        self.size = np.array(size)
        self.position = np.array(position)
        self.alignment = align
        self._drag_offset = None

        # Create the background of the panel.
        self.background = Rectangle2D(size=size, color=color, opacity=opacity)
        self.add_element(self.background, (0, 0))

        self.handle_events(self.background.actor)
        self.on_left_mouse_button_pressed = self.left_button_pressed
        self.on_left_mouse_button_dragged = self.left_button_dragged

    def add_to_renderer(self, ren):
        """ Allows UI objects to add their own props to the renderer.

        Here, we add only call add_to_renderer for the additional components.

        Parameters
        ----------
        ren : renderer

        """
        super(Panel2D, self).add_to_renderer(ren)
        for element in self._elements:
            element.add_to_renderer(ren)

    def get_actors(self):
        """ Returns the panel actor.

        """
        return []

    def add_element(self, element, coords):
        """ Adds a UI component to the panel.

        The coordinates represent an offset from the lower left corner of the
        panel.

        Parameters
        ----------
        element : UI
            The UI item to be added.
        coords : (float, float) or (int, int)
            If float, normalized coordinates are assumed and they must be
            between [0,1].
            If int, pixels coordinates are assumed and it must fit within the
            panel's size.

        """
        coords = np.array(coords)

        if np.issubdtype(coords.dtype, np.floating):
            if np.any(coords < 0) or np.any(coords > 1):
                raise ValueError("Normalized coordinates must be in [0,1].")

            coords = coords * self.size

        self._elements.append(element)
        self.element_positions.append((element, coords))
        element.position = self.position + coords

    def _set_position(self, coords):
        """ Position the lower-left corner of this UI component.

        Parameters
        ----------
        coords: (float, float)
            Absolute pixel coordinates (x, y).

        """
        coords = np.array(coords)
        for element, offset in self.element_positions:
            element.position = coords + offset

    @staticmethod
    def left_button_pressed(i_ren, obj, panel2d_object):
        click_pos = np.array(i_ren.event.position)
        panel2d_object._drag_offset = click_pos - panel2d_object.position
        i_ren.event.abort()  # Stop propagating the event.

    @staticmethod
    def left_button_dragged(i_ren, obj, panel2d_object):
        if panel2d_object._drag_offset is not None:
            click_position = np.array(i_ren.event.position)
            new_position = click_position - panel2d_object._drag_offset
            panel2d_object.position = new_position
        i_ren.force_render()

    def re_align(self, window_size_change):
        """ Re-organises the elements in case the window size is changed.

        Parameters
        ----------
        window_size_change : (int, int)
            New window size (width, height) in pixels.

        """
        if self.alignment == "left":
            pass
        elif self.alignment == "right":
            self.position += np.array(window_size_change)
        else:
            msg = "You can only left-align or right-align objects in a panel."
            raise ValueError(msg)


class TextBlock2D(UI):
    """ Wraps over the default vtkTextActor and helps setting the text.

    Contains member functions for text formatting.

    Attributes
    ----------
    actor : :class:`vtkTextActor`
        The text actor.
    message : str
        The initial text while building the actor.
    position : (float, float)
        (x, y) in pixels.
    color : (float, float, float)
        RGB: Values must be between 0-1.
    bg_color : (float, float, float)
        RGB: Values must be between 0-1.
    font_size : int
        Size of the text font.
    font_family : str
        Currently only supports Arial.
    justification : str
        left, right or center.
    vertical_justification : str
        bottom, middle or top.
    bold : bool
        Makes text bold.
    italic : bool
        Makes text italicised.
    shadow : bool
        Adds text shadow.
    """

    def __init__(self, text="Text Block", font_size=18, font_family='Arial',
                 justification='left', vertical_justification="bottom",
                 bold=False, italic=False, shadow=False,
                 color=(1, 1, 1), bg_color=None, position=(0, 0)):
        """
        Parameters
        ----------
        text : str
            The initial text while building the actor.
        position : (float, float)
            (x, y) in pixels.
        color : (float, float, float)
            RGB: Values must be between 0-1.
        bg_color : (float, float, float)
            RGB: Values must be between 0-1.
        font_size : int
            Size of the text font.
        font_family : str
            Currently only supports Arial.
        justification : str
            left, right or center.
        vertical_justification : str
            bottom, middle or top.
        bold : bool
            Makes text bold.
        italic : bool
            Makes text italicised.
        shadow : bool
            Adds text shadow.
        """
        super(TextBlock2D, self).__init__()
        self.actor = vtk.vtkTextActor()

        self._background = None  # For VTK < 7
        self.position = position
        self.color = color
        self.background_color = bg_color
        self.font_size = font_size
        self.font_family = font_family
        self.justification = justification
        self.bold = bold
        self.italic = italic
        self.shadow = shadow
        self.vertical_justification = vertical_justification
        self.message = text

    def get_actor(self):
        """ Returns the actor composing this element.

        Returns
        -------
        :class:`vtkTextActor`
            The actor composing this class.
        """
        return self.actor

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        if self._background is not None:
            return [self._background, self.actor]

        return [self.actor]

    @property
    def message(self):
        """ Gets message from the text.

        Returns
        -------
        str
            The current text message.

        """
        return self.actor.GetInput()

    @message.setter
    def message(self, text):
        """ Sets the text message.

        Parameters
        ----------
        text : str
            The message to be set.

        """
        self.actor.SetInput(text)

    @property
    def font_size(self):
        """ Gets text font size.

        Returns
        ----------
        int
            Text font size.

        """
        return self.actor.GetTextProperty().GetFontSize()

    @font_size.setter
    def font_size(self, size):
        """ Sets font size.

        Parameters
        ----------
        size : int
            Text font size.

        """
        self.actor.GetTextProperty().SetFontSize(size)

    @property
    def font_family(self):
        """ Gets font family.

        Returns
        ----------
        str
            Text font family.

        """
        return self.actor.GetTextProperty().GetFontFamilyAsString()

    @font_family.setter
    def font_family(self, family='Arial'):
        """ Sets font family.

        Currently Arial and Courier are supported.

        Parameters
        ----------
        family : str
            The font family.

        """
        if family == 'Arial':
            self.actor.GetTextProperty().SetFontFamilyToArial()
        elif family == 'Courier':
            self.actor.GetTextProperty().SetFontFamilyToCourier()
        else:
            raise ValueError("Font not supported yet: {}.".format(family))

    @property
    def justification(self):
        """ Gets text justification.

        Returns
        -------
        str
            Text justification.

        """
        justification = self.actor.GetTextProperty().GetJustificationAsString()
        if justification == 'Left':
            return "left"
        elif justification == 'Centered':
            return "center"
        elif justification == 'Right':
            return "right"

    @justification.setter
    def justification(self, justification):
        """ Justifies text.

        Parameters
        ----------
        justification : str
            Possible values are left, right, center.

        """
        text_property = self.actor.GetTextProperty()
        if justification == 'left':
            text_property.SetJustificationToLeft()
        elif justification == 'center':
            text_property.SetJustificationToCentered()
        elif justification == 'right':
            text_property.SetJustificationToRight()
        else:
            raise ValueError("Text can only be justified left, right and center.")

    @property
    def vertical_justification(self):
        """ Gets text vertical justification.

        Returns
        -------
        str
            Text vertical justification.

        """
        text_property = self.actor.GetTextProperty()
        vjustification = text_property.GetVerticalJustificationAsString()
        if vjustification == 'Bottom':
            return "bottom"
        elif vjustification == 'Centered':
            return "middle"
        elif vjustification == 'Top':
            return "top"

    @vertical_justification.setter
    def vertical_justification(self, vertical_justification):
        """ Justifies text vertically.

        Parameters
        ----------
        vertical_justification : str
            Possible values are bottom, middle, top.

        """
        text_property = self.actor.GetTextProperty()
        if vertical_justification == 'bottom':
            text_property.SetVerticalJustificationToBottom()
        elif vertical_justification == 'middle':
            text_property.SetVerticalJustificationToCentered()
        elif vertical_justification == 'top':
            text_property.SetVerticalJustificationToTop()
        else:
            msg = "Vertical justification must be: bottom, middle or top."
            raise ValueError(msg)

    @property
    def bold(self):
        """ Returns whether the text is bold.

        Returns
        -------
        bool
            Text is bold if True.

        """
        return self.actor.GetTextProperty().GetBold()

    @bold.setter
    def bold(self, flag):
        """ Bolds/un-bolds text.

        Parameters
        ----------
        flag : bool
            Sets text bold if True.

        """
        self.actor.GetTextProperty().SetBold(flag)

    @property
    def italic(self):
        """ Returns whether the text is italicised.

        Returns
        -------
        bool
            Text is italicised if True.

        """
        return self.actor.GetTextProperty().GetItalic()

    @italic.setter
    def italic(self, flag):
        """ Italicises/un-italicises text.

        Parameters
        ----------
        flag : bool
            Italicises text if True.

        """
        self.actor.GetTextProperty().SetItalic(flag)

    @property
    def shadow(self):
        """ Returns whether the text has shadow.

        Returns
        -------
        bool
            Text is shadowed if True.

        """
        return self.actor.GetTextProperty().GetShadow()

    @shadow.setter
    def shadow(self, flag):
        """ Adds/removes text shadow.

        Parameters
        ----------
        flag : bool
            Shadows text if True.

        """
        self.actor.GetTextProperty().SetShadow(flag)

    @property
    def color(self):
        """ Gets text color.

        Returns
        -------
        (float, float, float)
            Returns text color in RGB.

        """
        return self.actor.GetTextProperty().GetColor()

    @color.setter
    def color(self, color=(1, 0, 0)):
        """ Set text color.

        Parameters
        ----------
        color : (float, float, float)
            RGB: Values must be between 0-1.

        """
        self.actor.GetTextProperty().SetColor(*color)

    @property
    def background_color(self):
        """ Gets background color.

        Returns
        -------
        (float, float, float) or None
            If None, there no background color.
            Otherwise, background color in RGB.

        """
        if major_version < 7:
            if self._background is None:
                return None

            return self._background.GetProperty().GetColor()

        if self.actor.GetTextProperty().GetBackgroundOpacity() == 0:
            return None

        return self.actor.GetTextProperty().GetBackgroundColor()

    @background_color.setter
    def background_color(self, color):
        """ Set text color.

        Parameters
        ----------
        color : (float, float, float) or None
            If None, remove background.
            Otherwise, RGB values (must be between 0-1).

        """

        if color is None:
            # Remove background.
            if major_version < 7:
                self._background = None
            else:
                self.actor.GetTextProperty().SetBackgroundOpacity(0.)

        else:
            if major_version < 7:
                self._background = vtk.vtkActor2D()
                self._background.GetProperty().SetColor(*color)
                self._background.GetProperty().SetOpacity(1)
                self._background.SetMapper(self.actor.GetMapper())
                self._background.SetPosition(*self.actor.GetPosition())

            else:
                self.actor.GetTextProperty().SetBackgroundColor(*color)
                self.actor.GetTextProperty().SetBackgroundOpacity(1.)

    @property
    def position(self):
        """ Gets text actor position.

        Returns
        -------
        (float, float)
            The current actor position. (x, y) in pixels.

        """
        return self.actor.GetPosition()

    @position.setter
    def position(self, position):
        """ Set text actor position.

        Parameters
        ----------
        position : (float, float)
            The new position. (x, y) in pixels.

        """
        self.actor.SetPosition(*position)
        if self._background is not None:
            self._background.SetPosition(*self.actor.GetPosition())

    def set_center(self, position):
        """ Sets the text center to position.

        Parameters
        ----------
        position : (float, float)

        """
        self.position = position


class TextBox2D(UI):
    """ An editable 2D text box that behaves as a UI component.

    Currently supports:
    - Basic text editing.
    - Cursor movements.
    - Single and multi-line text boxes.
    - Pre text formatting (text needs to be formatted beforehand).

    Attributes
    ----------
    text : str
        The current text state.
    actor : :class:`vtkActor2d`
        The text actor.
    width : int
        The number of characters in a single line of text.
    height : int
        The number of lines in the textbox.
    window_left : int
        Left limit of visible text in the textbox.
    window_right : int
        Right limit of visible text in the textbox.
    caret_pos : int
        Position of the caret in the text.
    init : bool
        Flag which says whether the textbox has just been initialized.

    """
    def __init__(self, width, height, text="Enter Text", position=(100, 10),
                 color=(0, 0, 0), font_size=18, font_family='Arial',
                 justification='left', bold=False,
                 italic=False, shadow=False):
        """
        Parameters
        ----------
        width : int
            The number of characters in a single line of text.
        height : int
            The number of lines in the textbox.
        text : str
            The initial text while building the actor.
        position : (float, float)
            (x, y) in pixels.
        color : (float, float, float)
            RGB: Values must be between 0-1.
        font_size : int
            Size of the text font.
        font_family : str
            Currently only supports Arial.
        justification : str
            left, right or center.
        bold : bool
            Makes text bold.
        italic : bool
            Makes text italicised.
        shadow : bool
            Adds text shadow.

        """
        super(TextBox2D, self).__init__()
        self.text = text
        self.actor = self.build_actor(self.text, position, color, font_size,
                                      font_family, justification, bold, italic, shadow)
        self.width = width
        self.height = height
        self.window_left = 0
        self.window_right = 0
        self.caret_pos = 0
        self.init = True

        self.handle_events(self.actor.get_actor())

        self.on_left_mouse_button_pressed = self.left_button_press
        self.on_key_press = self.key_press

    def build_actor(self, text, position, color, font_size,
                    font_family, justification, bold, italic, shadow):

        """ Builds a text actor.

        Parameters
        ----------
        text : str
            The initial text while building the actor.
        position : (float, float)
            (x, y) in pixels.
        color : (float, float, float)
            RGB: Values must be between 0-1.
        font_size : int
            Size of the text font.
        font_family : str
            Currently only supports Arial.
        justification : str
            left, right or center.
        bold : bool
            Makes text bold.
        italic : bool
            Makes text italicised.
        shadow : bool
            Adds text shadow.

        Returns
        -------
        :class:`TextBlock2D`

        """
        text_block = TextBlock2D()
        text_block.position = position
        text_block.message = text
        text_block.font_size = font_size
        text_block.font_family = font_family
        text_block.justification = justification
        text_block.bold = bold
        text_block.italic = italic
        text_block.shadow = shadow

        if major_version >= 7:
            text_block.actor.GetTextProperty().SetBackgroundColor(1, 1, 1)
            text_block.actor.GetTextProperty().SetBackgroundOpacity(1.0)
            text_block.color = color

        return text_block

    def set_message(self, message):
        """ Set custom text to textbox.

        Parameters
        ----------
        message: str
            The custom message to be set.

        """
        self.text = message
        self.actor.message = message
        self.init = False
        self.window_right = len(self.text)
        self.window_left = 0
        self.caret_pos = self.window_right

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        return [self.actor.get_actor()]

    def width_set_text(self, text):
        """ Adds newlines to text where necessary.

        This is needed for multi-line text boxes.

        Parameters
        ----------
        text : str
            The final text to be formatted.

        Returns
        -------
        str
            A multi line formatted text.

        """
        multi_line_text = ""
        for i in range(len(text)):
            multi_line_text += text[i]
            if (i + 1) % self.width == 0:
                multi_line_text += "\n"
        return multi_line_text.rstrip("\n")

    def handle_character(self, character):
        """ Main driving function that handles button events.

        # TODO: Need to handle all kinds of characters like !, +, etc.

        Parameters
        ----------
        character : str

        """
        if character.lower() == "return":
            self.render_text(False)
            return True
        if character.lower() == "backspace":
            self.remove_character()
        elif character.lower() == "left":
            self.move_left()
        elif character.lower() == "right":
            self.move_right()
        else:
            self.add_character(character)
        self.render_text()
        return False

    def move_caret_right(self):
        """ Moves the caret towards right.

        """
        self.caret_pos = min(self.caret_pos + 1, len(self.text))

    def move_caret_left(self):
        """ Moves the caret towards left.

        """
        self.caret_pos = max(self.caret_pos - 1, 0)

    def right_move_right(self):
        """ Moves right boundary of the text window right-wards.

        """
        if self.window_right <= len(self.text):
            self.window_right += 1

    def right_move_left(self):
        """ Moves right boundary of the text window left-wards.

        """
        if self.window_right > 0:
            self.window_right -= 1

    def left_move_right(self):
        """ Moves left boundary of the text window right-wards.

        """
        if self.window_left <= len(self.text):
            self.window_left += 1

    def left_move_left(self):
        """ Moves left boundary of the text window left-wards.

        """
        if self.window_left > 0:
            self.window_left -= 1

    def add_character(self, character):
        """ Inserts a character into the text and moves window and caret accordingly.

        Parameters
        ----------
        character : str

        """
        if len(character) > 1 and character.lower() != "space":
            return
        if character.lower() == "space":
            character = " "
        self.text = (self.text[:self.caret_pos] +
                     character +
                     self.text[self.caret_pos:])
        self.move_caret_right()
        if (self.window_right -
                self.window_left == self.height * self.width - 1):
            self.left_move_right()
        self.right_move_right()

    def remove_character(self):
        """ Removes a character from the text and moves window and caret accordingly.

        """
        if self.caret_pos == 0:
            return
        self.text = self.text[:self.caret_pos - 1] + self.text[self.caret_pos:]
        self.move_caret_left()
        if len(self.text) < self.height * self.width - 1:
            self.right_move_left()
        if (self.window_right -
                self.window_left == self.height * self.width - 1):
            if self.window_left > 0:
                self.left_move_left()
                self.right_move_left()

    def move_left(self):
        """ Handles left button press.

        """
        self.move_caret_left()
        if self.caret_pos == self.window_left - 1:
            if (self.window_right -
                    self.window_left == self.height * self.width - 1):
                self.left_move_left()
                self.right_move_left()

    def move_right(self):
        """ Handles right button press.

        """
        self.move_caret_right()
        if self.caret_pos == self.window_right + 1:
            if (self.window_right -
                    self.window_left == self.height * self.width - 1):
                self.left_move_right()
                self.right_move_right()

    def showable_text(self, show_caret):
        """ Chops out text to be shown on the screen.

        Parameters
        ----------
        show_caret : bool
            Whether or not to show the caret.

        """
        if show_caret:
            ret_text = (self.text[:self.caret_pos] +
                        "_" +
                        self.text[self.caret_pos:])
        else:
            ret_text = self.text
        ret_text = ret_text[self.window_left:self.window_right + 1]
        return ret_text

    def render_text(self, show_caret=True):
        """ Renders text after processing.

        Parameters
        ----------
        show_caret : bool
            Whether or not to show the caret.

        """
        text = self.showable_text(show_caret)
        if text == "":
            text = "Enter Text"
        self.actor.message = self.width_set_text(text)

    def edit_mode(self):
        """ Turns on edit mode.

        """
        if self.init:
            self.text = ""
            self.init = False
            self.caret_pos = 0
        self.render_text()

    def set_center(self, position):
        """ Sets the text center to position.

        Parameters
        ----------
        position : (float, float)

        """
        self.actor.position = position

    @staticmethod
    def left_button_press(i_ren, obj, textbox_object):
        """ Left button press handler for textbox

        Parameters
        ----------
        i_ren: :class:`CustomInteractorStyle`
        obj: :class:`vtkActor`
            The picked actor
        textbox_object: :class:`TextBox2D`

        """
        i_ren.add_active_prop(textbox_object.actor.get_actor())
        textbox_object.edit_mode()
        i_ren.force_render()

    @staticmethod
    def key_press(i_ren, obj, textbox_object):
        """ Key press handler for textbox

        Parameters
        ----------
        i_ren: :class:`CustomInteractorStyle`
        obj: :class:`vtkActor`
            The picked actor
        textbox_object: :class:`TextBox2D`

        """
        key = i_ren.event.key
        is_done = textbox_object.handle_character(key)
        if is_done:
            i_ren.remove_active_prop(textbox_object.actor.get_actor())

        i_ren.force_render()


class LineSlider2D(UI):
    """ A 2D Line Slider.

    A sliding ring on a line with a percentage indicator.

    Currently supports:
    - A disk on a line (a thin rectangle).
    - Setting disk position.

    Attributes
    ----------
    line_width : int
        Width of the line on which the disk will slide.
    inner_radius : int
        Inner radius of the disk (ring).
    outer_radius : int
        Outer radius of the disk.
    center : (float, float)
        Center of the slider.
    length : int
        Length of the slider.
    slider_line : :class:`vtkActor`
        The line on which the slider disk moves.
    slider_disk : :class:`vtkActor`
        The moving slider disk.
    text : :class:`TextBlock2D`
        The text that shows percentage.

    """
    def __init__(self, line_width=5, inner_radius=0, outer_radius=10,
                 center=(450, 300), length=200, initial_value=50,
                 min_value=0, max_value=100, text_size=16,
                 text_template="{value:.1f} ({ratio:.0%})"):
        """
        Parameters
        ----------
        line_width : int
            Width of the line on which the disk will slide.
        inner_radius : int
            Inner radius of the disk (ring).
        outer_radius : int
            Outer radius of the disk.
        center : (float, float)
            Center of the slider.
        length : int
            Length of the slider.
        initial_value : float
            Initial value of the slider.
        min_value : float
            Minimum value of the slider.
        max_value : float
            Maximum value of the slider.
        text_size : int
            Size of the text to display alongside the slider (pt).
        text_template : str, callable
            If str, text template can contain one or multiple of the
            replacement fields: `{value:}`, `{ratio:}`.
            If callable, this instance of `:class:LineSlider2D` will be
            passed as argument to the text template function.

        """
        super(LineSlider2D, self).__init__()

        self.length = length
        self.min_value = min_value
        self.max_value = max_value

        self.text_template = text_template

        self.line_width = line_width
        self.center = center
        self.current_state = center[0]
        self.left_x_position = center[0] - length / 2
        self.right_x_position = center[0] + length / 2
        self._ratio = (self.current_state - self.left_x_position) / length

        self.slider_line = None
        self.slider_disk = None
        self.text = None

        self.build_actors(inner_radius=inner_radius,
                          outer_radius=outer_radius, text_size=text_size)

        # Setting the disk position will also update everything.
        self.value = initial_value
        # self.update()

        self.handle_events(None)

    def build_actors(self, inner_radius, outer_radius, text_size):
        """ Builds required actors.

        Parameters
        ----------
        inner_radius: int
            The inner radius of the sliding disk.
        outer_radius: int
            The outer radius of the sliding disk.
        text_size: int
            Size of the text that displays percentage.

        """
        # Slider Line
        rect = Rectangle2D(size=(self.length, self.line_width))
        rect.set_center(self.center)
        self.slider_line = rect.actor
        self.slider_line.GetProperty().SetColor(1, 0, 0)
        # /Slider Line

        # Slider Disk
        # Create source
        disk = vtk.vtkDiskSource()
        disk.SetInnerRadius(inner_radius)
        disk.SetOuterRadius(outer_radius)
        disk.SetRadialResolution(10)
        disk.SetCircumferentialResolution(50)
        disk.Update()

        # Mapper
        mapper = vtk.vtkPolyDataMapper2D()
        mapper.SetInputConnection(disk.GetOutputPort())

        # Actor
        self.slider_disk = vtk.vtkActor2D()
        self.slider_disk.SetMapper(mapper)
        # /Slider Disk

        # Slider Text
        self.text = TextBlock2D()
        self.text.position = (self.left_x_position - 50, self.center[1] - 10)
        self.text.font_size = text_size
        # /Slider Text

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        return [self.slider_line, self.slider_disk, self.text.get_actor()]

    def set_position(self, position):
        """ Sets the disk's position.

        Parameters
        ----------
        position : (float, float)
            The absolute position of the disk (x, y).

        """
        x_position = position[0]

        if x_position < self.center[0] - self.length/2:
            x_position = self.center[0] - self.length/2

        if x_position > self.center[0] + self.length/2:
            x_position = self.center[0] + self.length/2

        self.current_state = x_position
        self.update()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        value_range = self.max_value - self.min_value
        self.ratio = (value - self.min_value) / value_range

    @property
    def ratio(self):
        return self._ratio

    @ratio.setter
    def ratio(self, ratio):
        position_x = self.left_x_position + ratio*self.length
        self.set_position((position_x, None))

    def format_text(self):
        """ Returns formatted text to display along the slider. """
        if callable(self.text_template):
            return self.text_template(self)

        return self.text_template.format(ratio=self.ratio, value=self.value)

    def update(self):
        """ Updates the slider. """

        # Compute the ratio determined by the position of the slider disk.
        length = float(self.right_x_position - self.left_x_position)
        assert length == self.length
        self._ratio = (self.current_state - self.left_x_position) / length

        # Compute the selected value considering min_value and max_value.
        value_range = self.max_value - self.min_value
        self._value = self.min_value + self.ratio*value_range

        # Update text disk actor.
        self.slider_disk.SetPosition(self.current_state, self.center[1])

        # Update text.
        text = self.format_text()
        self.text.message = text
        offset_x = 8 * len(text) / 2.
        offset_y = 30
        self.text.position = (self.current_state - offset_x,
                              self.center[1] - offset_y)

    def set_center(self, position):
        """ Sets the center of the slider to position.

        Parameters
        ----------
        position : (float, float)
            The new center of the whole slider (x, y).

        """
        self.slider_line.SetPosition(position[0] - self.length / 2,
                                     position[1] - self.line_width / 2)

        x_change = position[0] - self.center[0]
        self.current_state += x_change
        self.center = position
        self.left_x_position = position[0] - self.length / 2
        self.right_x_position = position[0] + self.length / 2
        self.set_position((self.current_state, self.center[1]))

    @staticmethod
    def line_click_callback(i_ren, obj, slider):
        """ Update disk position and grab the focus.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        obj : :class:`vtkActor`
            The picked actor
        slider : :class:`LineSlider2D`

        """
        position = i_ren.event.position
        slider.set_position(position)
        i_ren.force_render()
        i_ren.event.abort()  # Stop propagating the event.

    @staticmethod
    def disk_press_callback(i_ren, obj, slider):
        """ Only need to grab the focus.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        obj : :class:`vtkActor`
            The picked actor
        slider : :class:`LineSlider2D`

        """
        i_ren.event.abort()  # Stop propagating the event.

    @staticmethod
    def disk_move_callback(i_ren, obj, slider):
        """ Actual disk movement.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        obj : :class:`vtkActor`
            The picked actor
        slider : :class:`LineSlider2D`

        """
        position = i_ren.event.position
        slider.set_position(position)
        i_ren.force_render()
        i_ren.event.abort()  # Stop propagating the event.

    def handle_events(self, actor):
        """ Handle all events for the LineSlider.
        Base method needs to be overridden due to multiple actors.

        """
        self.add_callback(self.slider_line, "LeftButtonPressEvent",
                          self.line_click_callback)
        self.add_callback(self.slider_disk, "LeftButtonPressEvent",
                          self.disk_press_callback)
        self.add_callback(self.slider_disk, "MouseMoveEvent",
                          self.disk_move_callback)
        self.add_callback(self.slider_line, "MouseMoveEvent",
                          self.disk_move_callback)


class DiskSlider2D(UI):
    """ A disk slider.

    A disk moves along the boundary of a ring.
    Goes from 0-360 degrees.

    Attributes
    ----------
    base_disk_center: (float, float)
        Position of the system.
    slider_inner_radius: int
        Inner radius of the base disk.
    slider_outer_radius: int
        Outer radius of the base disk.
    slider_radius: float
        Average radius of the base disk.
    handle_outer_radius: int
        Outer radius of the slider's handle.
    handle_inner_radius: int
        Inner radius of the slider's handle.

    """
    def __init__(self, position=(0, 0),
                 initial_value=180, min_value=0, max_value=360,
                 slider_inner_radius=40, slider_outer_radius=44,
                 handle_inner_radius=10, handle_outer_radius=0,
                 text_size=16,
                 text_template="{ratio:.0%}"):

        """
        Parameters
        ----------
        position : (float, float)
            Position (x, y) of the slider's center.
        initial_value : float
            Initial value of the slider.
        min_value : float
            Minimum value of the slider.
        max_value : float
            Maximum value of the slider.
        slider_inner_radius : int
            Inner radius of the base disk.
        slider_outer_radius : int
            Outer radius of the base disk.
        handle_outer_radius : int
            Outer radius of the slider's handle.
        handle_inner_radius : int
            Inner radius of the slider's handle.
        text_size : int
            Size of the text to display alongside the slider (pt).
        text_template : str, callable
            If str, text template can contain one or multiple of the
            replacement fields: `{value:}`, `{ratio:}`, `{angle:}`.
            If callable, this instance of `:class:DiskSlider2D` will be
            passed as argument to the text template function.

        """
        super(DiskSlider2D, self).__init__()
        self.center = np.array(position)
        self.min_value = min_value
        self.max_value = max_value

        self.slider_inner_radius = slider_inner_radius
        self.slider_outer_radius = slider_outer_radius
        self.handle_inner_radius = handle_inner_radius
        self.handle_outer_radius = handle_outer_radius
        self.slider_radius = (slider_inner_radius + slider_outer_radius) / 2.

        self.handle = None
        self.base_disk = None

        self.text = None
        self.text_size = text_size
        self.text_template = text_template

        self.build_actors()

        # By setting the value, it also updates everything.
        self.value = initial_value
        self.handle_events(None)

    def build_actors(self):
        """ Builds actors for the system.

        """
        base_disk = vtk.vtkDiskSource()
        base_disk.SetInnerRadius(self.slider_inner_radius)
        base_disk.SetOuterRadius(self.slider_outer_radius)
        base_disk.SetRadialResolution(10)
        base_disk.SetCircumferentialResolution(50)
        base_disk.Update()

        base_disk_mapper = vtk.vtkPolyDataMapper2D()
        base_disk_mapper.SetInputConnection(base_disk.GetOutputPort())

        self.base_disk = vtk.vtkActor2D()
        self.base_disk.SetMapper(base_disk_mapper)
        self.base_disk.GetProperty().SetColor(1, 0, 0)
        self.base_disk.SetPosition(self.center)

        handle = vtk.vtkDiskSource()
        handle.SetInnerRadius(self.handle_inner_radius)
        handle.SetOuterRadius(self.handle_outer_radius)
        handle.SetRadialResolution(10)
        handle.SetCircumferentialResolution(50)
        handle.Update()

        handle_mapper = vtk.vtkPolyDataMapper2D()
        handle_mapper.SetInputConnection(handle.GetOutputPort())

        self.handle = vtk.vtkActor2D()
        self.handle.SetMapper(handle_mapper)

        self.text = TextBlock2D()
        offset = np.array((16., 8.))
        self.text.position = self.center - offset
        self.text.font_size = self.text_size

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        value_range = self.max_value - self.min_value
        self.ratio = (value - self.min_value) / value_range

    @property
    def ratio(self):
        return self._ratio

    @ratio.setter
    def ratio(self, ratio):
        self.angle = ratio * TWO_PI

    @property
    def angle(self):
        """ Angle (in rad) the handle makes with x-axis """
        return self._angle

    @angle.setter
    def angle(self, angle):
        self._angle = angle % TWO_PI  # Wraparound
        self.update()

    def format_text(self):
        """ Returns formatted text to display along the slider. """
        if callable(self.text_template):
            return self.text_template(self)

        return self.text_template.format(ratio=self.ratio, value=self.value,
                                         angle=np.rad2deg(self.angle))

    def update(self):
        """ Updates the slider. """

        # Compute the ratio determined by the position of the slider disk.
        self._ratio = self.angle / TWO_PI

        # Compute the selected value considering min_value and max_value.
        value_range = self.max_value - self.min_value
        self._value = self.min_value + self.ratio*value_range

        # Update text disk actor.
        x = self.slider_radius * np.cos(self.angle) + self.center[0]
        y = self.slider_radius * np.sin(self.angle) + self.center[1]
        self.handle.SetPosition(x, y)

        # Update text.
        text = self.format_text()
        self.text.message = text

    def get_actors(self):
        """ Returns the actors that compose this UI component.

        """
        return [self.base_disk, self.handle, self.text.get_actor()]

    def move_handle(self, click_position):
        """Moves the slider's handle.

        Parameters
        ----------
        click_position: (float, float)
            Position of the mouse click.

        """
        x, y = np.array(click_position) - self.center
        angle = np.arctan2(y, x)
        if angle < 0:
            angle += TWO_PI

        self.angle = angle

    def set_center(self, position):
        """ Changes the slider's center position.

        Parameters
        ----------
        position : (float, float)
            New position (x, y).

        """
        position = np.array(position)
        offset = position - self.center
        self.base_disk.SetPosition(position)
        self.handle.SetPosition(*(offset + self.handle.GetPosition()))
        self.text.position += offset
        self.center = position

    @staticmethod
    def base_disk_click_callback(i_ren, obj, slider):
        """ Update disk position and grab the focus.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        obj : :class:`vtkActor`
            The picked actor
        slider : :class:`DiskSlider2D`

        """
        click_position = i_ren.event.position
        slider.move_handle(click_position=click_position)
        i_ren.force_render()
        i_ren.event.abort()  # Stop propagating the event.

    @staticmethod
    def handle_move_callback(i_ren, obj, slider):
        """ Move the slider's handle.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        obj : :class:`vtkActor`
            The picked actor
        slider : :class:`DiskSlider2D`

        """
        click_position = i_ren.event.position
        slider.move_handle(click_position=click_position)
        i_ren.force_render()
        i_ren.event.abort()  # Stop propagating the event.

    @staticmethod
    def handle_press_callback(i_ren, obj, slider):
        """ This is only needed to grab the focus.

        Parameters
        ----------
        i_ren : :class:`CustomInteractorStyle`
        obj : :class:`vtkActor`
            The picked actor
        slider : :class:`DiskSlider2D`

        """
        i_ren.event.abort()  # Stop propagating the event.

    def handle_events(self, actor):
        """ Handle all default slider events.

        """
        self.add_callback(self.base_disk, "LeftButtonPressEvent",
                          self.base_disk_click_callback)
        self.add_callback(self.handle, "LeftButtonPressEvent",
                          self.handle_press_callback)
        self.add_callback(self.base_disk, "MouseMoveEvent",
                          self.handle_move_callback)
        self.add_callback(self.handle, "MouseMoveEvent",
                          self.handle_move_callback)
