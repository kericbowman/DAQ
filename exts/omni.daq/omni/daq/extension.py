from logging import NullHandler
from typing import Text
import omni.ext
import omni.ui as ui
import omni.kit.commands as commands
from pxr import Usd, Tf

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):

    #define local variables
    def __init__(self):
        self.positionData = []
        self.positionPlot = ui.Plot()
        self.velocityData = []
        self.velocityPlot = ui.Plot()
        self.accelerationData = []
        self.accelerationPlot = ui.Plot()

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):

        self._window = ui.Window("Data Acquisition", width=600, height=400)
        with self._window.frame:
            with ui.VStack():                
                usd_context = omni.usd.get_context()
                stage = usd_context.get_stage()

                self.PrimPath = "/World/Sphere"

                with ui.Frame(alignment=ui.Alignment.CENTER):                
                    with ui.HStack():
                        ui.Label("Prim Path:  ", alignment=ui.Alignment.RIGHT, width=150)
                        model = ui.SimpleStringModel(self.PrimPath)
                        field = ui.StringField(model, width=300, alignment=ui.Alignment.LEFT)
                        #field.model.add_value_changed_fn(
                        #    lambda m, on_value(m))    
                        clear_btn = ui.Button("Clear Data", width=150)
                        clear_btn.set_clicked_fn(
                            lambda b=clear_btn:self.clear_clicked()) 

                ui.Label("Prim Y Position", alignment=ui.Alignment.CENTER)
                                
                self.positionData.append(0.0)
                self.positionPlot =  ui.Plot(ui.Type.LINE, -1000.0, 1000.0, *self.positionData, width=600, height=100, 
                    alignment=ui.Alignment.CENTER, style={"color": 0xFF0000FF})

                ui.Label("Prim Y Velocity", alignment=ui.Alignment.CENTER)
                                
                self.velocityData.append(0.0)
                self.velocityPlot = ui.Plot(ui.Type.LINE, -2000.0, 2000.0, *self.velocityData, width=600, height=100, 
                    alignment=ui.Alignment.CENTER, style={"color": 0xFF0000FF})

                ui.Label("Prim Y Acceleration", alignment=ui.Alignment.CENTER)
                                
                self.accelerationData.append(0.0)
                self.accelerationPlot =  ui.Plot(ui.Type.LINE, -10000.0, 10000.0, *self.accelerationData, width=600, height=100, 
                    alignment=ui.Alignment.CENTER, style={"color": 0xFF0000FF})

                self.previousPos = 0.0
                self.previousVelocity = 0.0

                self._stasge_listener = Tf.Notice.Register(
                    Usd.Notice.ObjectsChanged, self._notice_changed, stage)      
        
    def on_value(self, model):
        self.PrimPath = model.get_value()

    def clear_clicked(self):
        self.positionData.clear()
        self.positionData.append(0.0)
        self.positionPlot.set_data(*self.positionData)
        self.velocityData.clear()
        self.velocityData.append(0.0)
        self.velocityPlot.set_data(*self.velocityData)
        self.accelerationData.clear()
        self.accelerationData.append(0.0)
        self.accelerationPlot.set_data(*self.accelerationData)

    def on_shutdown(self):
        print("[omni.daq] MyExtension shutdown")
        
    def _notice_changed(self, notice, stage):
        for p in notice.GetChangedInfoOnlyPaths():
            if p.GetPrimPath() == self.PrimPath:
                
                timeline = omni.timeline.get_timeline_interface()
                timecode = timeline.get_current_time() * timeline.get_time_codes_per_seconds()
                
                #Simplifying Assumption: 60 frames per second
                elapsedTime = 0.016667
                
                prim = stage.GetPrimAtPath(self.PrimPath)
                pose = omni.usd.utils.get_world_transform_matrix(prim, timecode)
                                
                nextPos = pose.ExtractTranslation()[1]

                if nextPos != self.previousPos:

                    nextVelocity = (nextPos - self.previousPos) / elapsedTime
                    yAcceleration = (nextVelocity - self.previousVelocity) / elapsedTime

                    self.previousPos = nextPos
                    self.previousVelocity = nextVelocity

                    self.positionData.append(nextPos)
                    self.positionPlot.set_data(*self.positionData)

                    self.velocityData.append(nextVelocity)     
                    self.velocityPlot.set_data(*self.velocityData)

                    self.accelerationData.append(yAcceleration)     
                    self.accelerationPlot.set_data(*self.accelerationData)
