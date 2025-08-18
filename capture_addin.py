# coding: utf-8
import arcpy
import pythonaddins
import os,json
import tempfile
import urllib2,urllib
import datetime
# 全局变量：存储当前选中的图层名
selected_layer_name = ""
point_list=[]
values=[]

class ComboBoxClass10(object):
    """Implementation for capture_addin.combobox (ComboBox)"""
    def __init__(self):
        # self.value="item1"
        self.items = ["item1", "item2"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWW'
        self._refresh_layers()
    
    def _refresh_layers(self):
        global selected_layer_name
        """刷新图层列表"""
        self.items = []
        try:
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = mxd.activeDataFrame
            layers = arcpy.mapping.ListLayers(mxd, data_frame=df)
            self.items = [lyr.name for lyr in layers if lyr.isFeatureLayer or lyr.isRasterLayer]
            print(self.items)
            print(selected_layer_name)
        except:
            self.items = []
        # 如果当前选中的图层不在列表中，清空选择
        if selected_layer_name not in self.items:
            print("the selected not in items")
            selected_layer_name = ""
    def onSelChange(self, selection):
        # self.value=selection
        global selected_layer_name
        selected_layer_name = selection  # 更新全局变量
        print(u"已选择图层: "+selected_layer_name)
        self.refresh()
    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        # editable为true时，可用
        """当控件获得焦点时刷新图层列表"""
        if focused:
            self._refresh_layers()
            # 更新下拉选项
            # print("LayerComboBox"+ self.items)
    def onEnter(self):
        pass
    def refresh(self):
        self._refresh_layers()
        # print("LayerComboBox"+ self.items)
        pass

class tool8(object):
    """Implementation for capture_addin.tool (Tool)"""
    def __init__(self):
        self.enabled = True
        self.shape = "NONE" # Can set to "Line", "Circle" or "Rectangle" for interactive shape drawing and to activate the onLine/Polygon/Circle event sinks.
    def onMouseDown(self, x, y, button, shift):
        pass
    def onMouseDownMap(self, x, y, button, shift):
        global selected_layer_name  # 读取全局变量
        global point_list
        global values        
        if button == 1:  # 左键
            if shift:
                print("shift+left click")
                values.append(-1)
                point_list.append([x,y])
            else:
                print("left click")
                values.append(1)
                point_list.append([x,y])           
    def log(self,msg):
        with open(r"C:\temp\add_in_log.txt", "a") as f:
            f.write("{}: {}\n".format(datetime.datetime.now().strftime("%H:%M:%S"), msg))
        
    def create_polygon_from_coordinates(self,coordinates, spatial_reference):
        """
        根据给定的坐标串创建一个Polygon对象。
        
        :param coordinates: 嵌套列表形式的坐标串
        :param spatial_reference: 空间参考信息
        :return: Polygon几何对象
        [[[507533.2519248578, 3231029.840414506]],[[507533.01862252486, 3231030.0738246264]],[[507531.8521108602, 3231030.0738246264]],[[507531.6188085273, 3231030.3072347464]],[[507531.3855061944, 3231030.3072347464]],[[507533.2519248578, 3231029.840414506]]]
        """
        # 处理输入的坐标串
        
        part_array = []
        for part in coordinates:
            # self.log(part)
            x, y = part[0]
            newPoint=arcpy.Point(x, y)
            # # 闭合多边形
            # if not part_array[0].equals(part_array[-1]):
            #     part_array.append(part_array[0])
            part_array.append(newPoint)
        array = arcpy.Array(part_array)
        return arcpy.Polygon(array, spatial_reference)
    def onMouseUp(self, x, y, button, shift):
        pass
    def onMouseUpMap(self, x, y, button, shift):
        pass
    def onMouseMove(self, x, y, button, shift):
        pass
    def onMouseMoveMap(self, x, y, button, shift):
        pass
    def onDblClick(self):
        global selected_layer_name  # 读取全局变量
        global point_list
        global values
        
        if not selected_layer_name:
            pythonaddins.MessageBox(u"请先在下拉框中选择一个图层！", u"提示")
            return

        # 获取当前地图文档和活动数据框
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = mxd.activeDataFrame

        # 查找图层
        layers = arcpy.mapping.ListLayers(mxd, selected_layer_name, df)
        if not layers:
            pythonaddins.MessageBox(u"未找到图层：{}，请检查名称是否正确。".format(selected_layer_name), u"错误")
            return

        layer = layers[0]

        # 检查是否为矢量图层（Feature Layer）
        if not layer.isFeatureLayer:
            pythonaddins.MessageBox(u"所选图层 '{}' 不是矢量图层。".format(selected_layer_name), u"类型错误")
            return

        # 检查几何类型是否为面（Polygon）
        desc = arcpy.Describe(layer)
        if desc.shapeType != "Polygon":
            pythonaddins.MessageBox(u"所选图层 '{}' 不是面图层，当前类型为：{}。".format(selected_layer_name, desc.shapeType), u"类型错误")
            return
        try:
            # 1. get current map document
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = arcpy.mapping.ListDataFrames(mxd)[0]  # main data frame

            # 2. create a temporary directory to save a shotscreen
            temp_dir = tempfile.gettempdir()
            png_filename = "arcgis_capture.png"
            png_path = os.path.join(temp_dir, png_filename)

            # get current extent
            extent = df.extent

            # get corners' positions
            left = extent.XMin
            bottom = extent.YMin
            right = extent.XMax
            top = extent.YMax

            arcpy.AddMessage("coners' positions:"+str(left)+","+str(bottom)+","+str(right)+","+str(top))
            # 3. shotscreen to PNG
            # set output size
            output_width_px = 1920
            output_height_px = int(output_width_px * (extent.height / extent.width))

            arcpy.mapping.ExportToPNG(
                mxd,
                png_path,
                data_frame=df,
                df_export_width=output_width_px,
                df_export_height=output_height_px,
            )

            if not os.path.exists(png_path):
                pythonaddins.MessageBox(u"截图失败！", u"错误")
                return

            arcpy.AddMessage("shotscreen has been saved at "+png_path)

            # 4. upload picture
            upload_url = "http://localhost:50005/upload"  
            field_name = "image"  

            try:
                formdata = {
                    "photo":png_path,
                    "point":point_list,
                    "values":values,
                    "corners":[left,bottom,right,top],
                    "img_width":output_width_px,
                    "img_height":output_height_px
                }

                data = urllib.urlencode(formdata)

                request = urllib2.Request(upload_url, data = data)
                response = urllib2.urlopen(request)
        
                response_text =response.read() # self.upload_file(upload_url, field_name, png_path)
                
                # self.log(json.loads(response_text)['feature'])
                # self.log(desc.spatialReference)
                # 创建几何对象
                polygon_geom = self.create_polygon_from_coordinates(json.loads(response_text)['feature'], desc.spatialReference)
                point_list=[]
                values=[]
                try:
                    # 使用 InsertCursor 插入新要素
                    with arcpy.da.InsertCursor(layer, ["SHAPE@"]) as cursor:
                        cursor.insertRow([polygon_geom])

                    # pythonaddins.MessageBox(u"已成功向图层 '{}' 插入一条面要素！".format(selected_layer_name), u"成功")

                    # 刷新显示
                    arcpy.RefreshActiveView()

                except Exception as e:
                    pythonaddins.MessageBox(u"插入失败: " + str(e), u"错误")
    
    
                # pythonaddins.MessageBox("上传成功！\n响应: " + response_text, "成功")
                # response_text =self.upload_file(upload_url, field_name, png_path)
                # pythonaddins.MessageBox(u"上传成功！\n响应: " + response_text, u"成功")
            except Exception as e:
                pythonaddins.MessageBox(u"上传失败: " + str(e), u"错误")

        except Exception as e:
            pythonaddins.MessageBox(u"操作失败: " + str(e), u"错误")
    def onKeyDown(self, keycode, shift):
        pass
    def onKeyUp(self, keycode, shift):
        pass
    def deactivate(self):
        global point_list
        global values
        point_list=[]
        values=[]
        pass
    def onCircle(self, circle_geometry):
        pass
    def onLine(self, line_geometry):
        pass
    def onRectangle(self, rectangle_geometry):
        pass