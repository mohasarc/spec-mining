# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION
from nltk.draw.util import CanvasFrame, CanvasWidget, SequenceWidget
from tkinter import Tk

class CreateWidgetOnSameFrameCanvas(Spec):
    """
    This specification ensures that canvas widgets are added only to the CanvasFrame's designated canvas
    source: https://www.nltk.org/api/nltk.draw.util.html#nltk.draw.util.CanvasFrame.add_widget
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(CanvasFrame, 'add_widget'))
        def widgetAdded(**kw):
            args = kw['args']
            kwargs = kw['kwargs']

            canvasFrame = kw['obj']
            canvasWidget = None

            if len(args) > 1:
                canvasWidget = args[1]
            else:
                canvasWidget = kwargs['canvaswidget']

            fCanvas = canvasFrame.canvas()
            wCanvas = canvasWidget.canvas()

            if wCanvas.winfo_id() != fCanvas.winfo_id():
                return {'verdict': VIOLATION, 
                        'custom_message': f"CanvasWidget must be created on the same canvas as the CanvasFrame it is being added to at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}


    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: CanvasWidget must be created on the same canvas as the CanvasFrame it is being added to.'
            f'File {call_file_name}, line {call_line_num}.')


# =========================================================================
