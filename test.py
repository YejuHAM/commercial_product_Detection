 package main

 import (
 	"fmt"
 	"image"
 	"image/color"
 	"image/draw"
 	"io/ioutil"
 	"log"
 	"runtime"
 	"strconv"
 	"time"

 	"github.com/lazywei/go-opencv/opencv"
 	"github.com/mattn/go-gtk/glib"
 	"github.com/mattn/go-gtk/gtk"

 	"github.com/golang/freetype"
 	"github.com/golang/freetype/truetype"
 )

 var (
 	win                      = new(opencv.Window)
 	webCamera                = new(opencv.Capture)
 	statusbar                = new(gtk.Statusbar)
 	snapshotFileName         string
 	width, height            int
 	sliderPosX, sliderPosY   int
 	stopCamera               = false // to prevent segmentation fault
 	backgroundWidth          = 650
 	backgroundHeight         = 150
 	horizontalScale          = float32(1.0)
 	verticalScale            = float32(1.0)
 	shear                    = float32(1.0)
 	thickness                = 3
 	lineType                 = 8
 	textFont                 = opencv.InitFont(opencv.CV_FONT_HERSHEY_SIMPLEX, horizontalScale, verticalScale, shear, thickness, lineType)
 	utf8FontFile             = "wqy-zenhei.ttf"
 	utf8FontSize             = float64(30.0)
 	spacing                  = float64(1.5)
 	dpi                      = float64(72)
 	ctx                      = new(freetype.Context)
 	utf8Font                 = new(truetype.Font)
 	IplImgFrame, utf8TextImg *opencv.IplImage
 	redColor                 = opencv.NewScalar(0, 0, 255, 0)   // red - (blue, green, red, alpha)
 	cyanColor                = opencv.NewScalar(255, 255, 0, 0) // cyan - (blue, green, red, alpha)
 	red                      = color.RGBA{255, 0, 0, 255}
 	blue                     = color.RGBA{0, 0, 255, 255}
 	white                    = color.RGBA{255, 255, 255, 255}
 	black                    = color.RGBA{0, 0, 0, 255}
 	background               *image.RGBA
 	// more color at https://github.com/golang/image/blob/master/colornames/table.go
 )

 func opencvImageBGRToBGRA(img *opencv.IplImage) opencv.IplImage {
 	// The image frames from camera is in RGB (3 channels )
 	// We need to convert the frames to RGBA (4 channels )
 	// so that we can perform copy and paste the UTF8 strings
 	// into the region of interest.
 	// Using the ToImage() function will work, but will cause delay in refresh rate.
 	// Use CvtColor() function for the best result

 	//fmt.Println("img channels : ", img.Channels())

 	w := img.Width()
 	h := img.Height()

 	// create a IplImage with 4 channels
 	tmp := opencv.CreateImage(w, h, opencv.IPL_DEPTH_8U, 4)

 	// upgrade BGR to BGRA ( 3 to 4 channels)
 	opencv.CvtColor(img, tmp, opencv.CV_BGR2BGRA)
 	//fmt.Println("tmp channels : ", tmp.Channels())
 	return *tmp

 }

 func BGRAToBGR(img *opencv.IplImage) opencv.IplImage {

 	w := img.Width()
 	h := img.Height()

 	// create a IplImage with 3 channels
 	tmp := opencv.CreateImage(w, h, opencv.IPL_DEPTH_8U, 3)

 	// downgrade BGRA to BGR ( 4 to 3 channels)
 	opencv.CvtColor(img, tmp, 1)
 	// why use integer value of 1?
 	// see http://docs.opencv.org/3.1.0/df/d4e/group__imgproc__c.html
 	return *tmp

 }

 func processFrameAndUpdate() {

 	var UTF8text = []string{
 		`©, 世界,Мир,World,세계,Dunia,κόσμος`,
 		`全世界 愛Go語, Весь мир любовь golang`,
 		`Όλος ο κόσμος αγάπη golang,전세계 Go언어`,
 	}

 	// Draw the text to the background
 	pt := freetype.Pt(10, 10+int(ctx.PointToFixed(utf8FontSize)>>6))

 	// not all utf8 fonts are supported by wqy-zenhei.ttf
 	// use your own language true type font file if your language cannot be printed

 	for _, str := range UTF8text {
 		_, err := ctx.DrawString(str, pt)
 		if err != nil {
 			fmt.Println(err)
 			return
 		}
 		pt.Y += ctx.PointToFixed(utf8FontSize * spacing)
 	}

 	// convert background from image.Image type to opencv.IplImage
 	utf8TextImg = opencv.FromImage(background)

 	// after converting to opencv IplImage...the transparency is gone!
 	// test := utf8TextImg.ToImage()

 	// any way to make the UTF8 string to have transparent background ??
 	// maybe http://stackoverflow.com/questions/32350604/create-a-transparent-image-in-opencv

 	for {

 		if webCamera.GrabFrame() && !stopCamera {
 			IplImgFrame = webCamera.RetrieveFrame(1)
 			if IplImgFrame != nil {

 				// we need to convert IplImgFrame number of
 				// channels to 4 instead of 3.
 				// otherwise the opencv.Copy() function below will crash...

 				*IplImgFrame = opencvImageBGRToBGRA(IplImgFrame)

 				// see https://www.socketloop.com/tutorials/golang-get-current-time
 				currentTime := time.Now().Local().Format("2006-01-02 15:04:05 +0800")

 				// set ROI(Region Of Interest) in IplImageFrame
 				rect := opencv.NewRect(sliderPosX, sliderPosY, backgroundWidth, backgroundHeight)
 				IplImgFrame.SetROI(rect)

 				// copy and paste our UTF8 runes into ROI via Copy
 				opencv.Copy(utf8TextImg, IplImgFrame, nil)
 				IplImgFrame.ResetROI() // don't forget this!
 				opencv.Rectangle(IplImgFrame,
 					opencv.Point{sliderPosX + backgroundWidth, sliderPosY},
 					opencv.Point{sliderPosX, sliderPosY + backgroundHeight},
 					opencv.ScalarAll(0.0), 2, 2, 0)

 				//position := opencv.Point{sliderPosX, sliderPosY}
 				//textFont.PutText(IplImgFrame, "Hello World!", position, redColor)
 				textFont.PutText(IplImgFrame, currentTime, opencv.Point{sliderPosX, sliderPosY + int(verticalScale*200.0)}, cyanColor)

 				win.ShowImage(IplImgFrame)

 			}
 		}

 	}

 }

 func main() {

 	cores := runtime.NumCPU()

 	fmt.Printf("This machine has %d CPU cores. Using all cores. \n", cores)

 	// maximize CPU usage for maximum performance
 	runtime.GOMAXPROCS(cores)

 	// download font from http://www.slackware.com/~alien/slackbuilds/wqy-zenhei-font-ttf/build/wqy-zenhei-0.4.23-1.tar.gz
 	// extract wqy-zenhei.ttf to the same folder as this program

 	// Read the font data - for this example, we load the Chinese fontfile wqy-zenhei.ttf,
 	// but it will display any utf8 fonts such as Russian, Japanese, Korean, etc as well.
 	// some utf8 fonts cannot be displayed. You need to use your own language .ttf file
 	fontBytes, err := ioutil.ReadFile(utf8FontFile)
 	if err != nil {
 		log.Println(err)
 		return
 	}

 	utf8Font, err = freetype.ParseFont(fontBytes)
 	if err != nil {
 		log.Println(err)
 		return
 	}

 	// we use red on white to make our text more visible in the camera video feed
 	// if you plan to use the fontForeGroundColor only. Setting background to transparent with image.Transparent
 	// will cause it to appear as black on camera feed. Why? because the OpenCV camera video capture images' color model cannot
 	// support transparency. See https://blog.golang.org/go-imagedraw-package.

 	//fontForeGroundColor, fontBackGroundColor := image.NewUniform(white), image.Transparent

 	fontForeGroundColor, fontBackGroundColor := image.NewUniform(red), image.NewUniform(white)

 	background = image.NewRGBA(image.Rect(0, 0, backgroundWidth, backgroundHeight))

 	draw.Draw(background, background.Bounds(), fontBackGroundColor, image.ZP, draw.Src)

 	ctx = freetype.NewContext()
 	ctx.SetDPI(dpi) //screen resolution in Dots Per Inch
 	ctx.SetFont(utf8Font)
 	ctx.SetFontSize(utf8FontSize) //font size in points
 	ctx.SetClip(background.Bounds())
 	ctx.SetDst(background)
 	ctx.SetSrc(fontForeGroundColor)
 	// the rest will be inside processFrameAndUpdate() function

 	// a new OpenCV window
 	win = opencv.NewWindow("Display UTF8 text or runes on Go-OpenCV camera feed")
 	defer win.Destroy()

 	// activate webCamera
 	webCamera = opencv.NewCameraCapture(opencv.CV_CAP_ANY) // autodetect

 	if webCamera == nil {
 		panic("Unable to open camera")
 	}

 	defer webCamera.Release()

 	// get some data from camera
 	width = int(webCamera.GetProperty(opencv.CV_CAP_PROP_FRAME_WIDTH))
 	height = int(webCamera.GetProperty(opencv.CV_CAP_PROP_FRAME_HEIGHT))

 	fmt.Println("Camera width : ", width)
 	fmt.Println("Camera height : ", height)

 	// open up a new "pure" OpenCV window first
 	go processFrameAndUpdate() // goroutine to update feed from camera

 	// then our "floating" GTK toolbar
 	gtk.Init(nil)
 	window := gtk.NewWindow(gtk.WINDOW_TOPLEVEL)

 	window.SetPosition(gtk.WIN_POS_CENTER)
 	window.SetTitle("Example of writing UTF8 text on Go-OpenCV video capture!")
 	window.SetIconName("gtk-dialog-info")
 	window.Connect("destroy", func(ctx *glib.CallbackContext) {
 		println("got destroy!", ctx.Data().(string))
 		gtk.MainQuit()
 	}, "Happy coding!")

 	vbox := gtk.NewVBox(false, 1)

 	//--------------------------------------------------------
 	// GtkVPaned
 	//--------------------------------------------------------
 	vpaned := gtk.NewVPaned()
 	vbox.Add(vpaned)

 	//--------------------------------------------------------
 	// GtkFrame
 	//--------------------------------------------------------

 	frame1 := gtk.NewFrame("Adjust X & Y co-ordinates to place the text location :")
 	framebox1 := gtk.NewVBox(false, 1)
 	frame1.Add(framebox1)

 	//--------------------------------------------------------
 	// GtkScale
 	//--------------------------------------------------------
 	scaleXHBox := gtk.NewHBox(false, 1)

 	scaleX := gtk.NewHScaleWithRange(0, float64(width), 1)
 	scaleX.Connect("value-changed", func() {
 		//println("scale:", int(scale.GetValue()))
 		sliderPosX = int(scaleX.GetValue())
 		statusbar.Push(statusbar.GetContextId("go-gtk"), "X : "+strconv.Itoa(sliderPosX)+" Y : "+strconv.Itoa(sliderPosY))
 	})
 	scaleXHBox.Add(scaleX)
 	framebox1.PackStart(scaleXHBox, false, false, 0)

 	scaleYHBox := gtk.NewHBox(false, 1)

 	scaleY := gtk.NewHScaleWithRange(0, float64(height), 1)
 	scaleY.Connect("value-changed", func() {
 		//println("scale:", int(scale.GetValue()))
 		sliderPosY = int(scaleY.GetValue())
 		statusbar.Push(statusbar.GetContextId("go-gtk"), "X : "+strconv.Itoa(sliderPosX)+" Y : "+strconv.Itoa(sliderPosY))
 	})
 	scaleYHBox.Add(scaleY)
 	framebox1.PackStart(scaleYHBox, false, false, 0)

 	vpaned.Pack1(frame1, false, false)

 	//--------------------------------------------------------
 	// GtkHBox
 	//--------------------------------------------------------
 	buttons := gtk.NewHBox(false, 1)

 	//--------------------------------------------------------
 	// GtkButton
 	//--------------------------------------------------------

 	quitButton := gtk.NewButtonWithLabel("Quit")
 	quitButton.Clicked(func() {
 		stopCamera = true
 		webCamera.Release() // don't forget to release !!
 		gtk.MainQuit()
 	})

 	buttons.Add(quitButton)
 	framebox1.PackStart(buttons, false, false, 0)

 	//--------------------------------------------------------
 	// GtkVSeparator
 	//--------------------------------------------------------
 	vsep := gtk.NewVSeparator()
 	framebox1.PackStart(vsep, false, false, 0)

 	statusbar = gtk.NewStatusbar()
 	//context_id := statusbar.GetContextId("go-gtk")

 	//--------------------------------------------------------
 	// GtkStatusbar
 	//--------------------------------------------------------
 	framebox1.PackStart(statusbar, false, false, 0)

 	//--------------------------------------------------------
 	// Event
 	//--------------------------------------------------------
 	window.Add(vbox)
 	window.SetSizeRequest(600, 128)
 	window.ShowAll()

 	gtk.Main()

 }