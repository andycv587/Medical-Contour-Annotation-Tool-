/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.WatershedMethod;

import Contours.annotation.CustomImgPanel;
import Contours.annotation.Mask;
import Contours.annotation.Utility;
import java.awt.image.BufferedImage;
import java.awt.image.DataBufferByte;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.Vector;
import javax.imageio.ImageIO;
import org.opencv.core.Core;
import org.opencv.core.CvType;
import org.opencv.core.Mat;
import org.opencv.core.MatOfPoint;
import org.opencv.core.Point;
import org.opencv.core.Scalar;
import org.opencv.highgui.HighGui;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;

public class Watershed {

    private int klength_x = 10;
    private int klength_y = 10;
    private int highThreshold = 255;
    private int lowThreshold = 40;
    private Mat marker;

    private Mat file;
    private Vector<Mask> masks;
    private CustomImgPanel pane;
//
//    public static void main(String[] args) {
//        Watershed wtsd = new Watershed(3, 3, 255, 10);
//        wtsd.run();
//
//    }

    public Watershed(int klength_x, int klength_y, int highThreshold, int lowThreshold, Mat file, CustomImgPanel pane) {
        this.klength_x = klength_x;
        this.klength_y = klength_y;
        this.highThreshold = highThreshold;
        this.lowThreshold = lowThreshold;
        this.file = file;
        this.pane = pane;
        this.masks=new Vector<Mask>();
    }

//    public Watershed(int klength_x, int klength_y, int highThreshold, int lowThreshold) {
//        System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
//        this.klength_x = klength_x;
//        this.klength_y = klength_y;
//        this.highThreshold = highThreshold;
//        this.lowThreshold = lowThreshold;
//        this.file = Imgcodecs.imread("D:\\11111.png");
//    }

//    
//    public static void main(String[] args){
//        System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
//        Mat ma=Imgcodecs.imread("D:\\Conference\\2022SPIE\\Results\\exp_folder\\brain_1\\oripng\\1-10.png");
//        Watershed ws=new Watershed(ma.rows(),ma.cols(),230,100,ma);
//        ws.run();
//    }
//    
//    
    public void run() throws IOException {
        // Load the imag
        Mat srcOriginal = file;
        // Show source image
//        HighGui.imshow("Source Image", srcOriginal);
        // Change the background from white to black, since that will help later to
        // extract
        // better results during the use of Distance Transform
        Mat src = srcOriginal.clone();
        byte[] srcData = new byte[(int) (src.total() * src.channels())];
        src.get(0, 0, srcData);
        for (int i = 0; i < src.rows(); i++) {
            for (int j = 0; j < src.cols(); j++) {
                if (srcData[(i * src.cols() + j) * 3] == (byte) 255 && srcData[(i * src.cols() + j) * 3 + 1] == (byte) 255
                        && srcData[(i * src.cols() + j) * 3 + 2] == (byte) 255) {
                    srcData[(i * src.cols() + j) * 3] = 0;
                    srcData[(i * src.cols() + j) * 3 + 1] = 0;
                    srcData[(i * src.cols() + j) * 3 + 2] = 0;
                }
            }
        }
        src.put(0, 0, srcData);
        // Show output image
//        HighGui.imshow("Black Background Image", src);
        // Create a kernel that we will use to sharpen our image
        Mat kernel = new Mat(klength_x, klength_y, CvType.CV_32F);
        // an approximation of second derivative, a quite strong kernel
        float[] kernelData = new float[(int) (kernel.total() * kernel.channels())];
        kernelData[0] = 1;
        kernelData[1] = 1;
        kernelData[2] = 1;
        kernelData[3] = 1;
        kernelData[4] = -8;
        kernelData[5] = 1;
        kernelData[6] = 1;
        kernelData[7] = 1;
        kernelData[8] = 1;
        kernel.put(0, 0, kernelData);
        // do the laplacian filtering as it is
        // well, we need to convert everything in something more deeper then CV_8U
        // because the kernel has some negative values,
        // and we can expect in general to have a Laplacian image with negative values
        // BUT a 8bits unsigned int (the one we are working with) can contain values
        // from 0 to 255
        // so the possible negative number will be truncated
        Mat imgLaplacian = new Mat();
        Imgproc.filter2D(src, imgLaplacian, CvType.CV_32F, kernel);
        Mat sharp = new Mat();
        src.convertTo(sharp, CvType.CV_32F);
        Mat imgResult = new Mat();
        Core.subtract(sharp, imgLaplacian, imgResult);
        // convert back to 8bits gray scale
        imgResult.convertTo(imgResult, CvType.CV_8UC3);
        imgLaplacian.convertTo(imgLaplacian, CvType.CV_8UC3);
        // imshow( "Laplace Filtered Image", imgLaplacian );
//        HighGui.imshow("New Sharped Image", imgResult);
        // Create binary image from source image
        Mat bw = new Mat();
        Imgproc.cvtColor(imgResult, bw, Imgproc.COLOR_BGR2GRAY);
        Imgproc.threshold(bw, bw, lowThreshold, highThreshold, Imgproc.THRESH_BINARY | Imgproc.THRESH_OTSU);
//        HighGui.imshow("Binary Image", bw);
        // Perform the distance transform algorithm
        Mat dist = new Mat();
        Imgproc.distanceTransform(bw, dist, Imgproc.DIST_L2, 3);
        // Normalize the distance image for range = {0.0, 1.0}
        // so we can visualize and threshold it
        Core.normalize(dist, dist, 0.0, 1.0, Core.NORM_MINMAX);
        Mat distDisplayScaled = new Mat();
        Core.multiply(dist, new Scalar(255), distDisplayScaled);
        Mat distDisplay = new Mat();
        distDisplayScaled.convertTo(distDisplay, CvType.CV_8U);
//        HighGui.imshow("Distance Transform Image", distDisplay);
        // Threshold to obtain the peaks
        // This will be the markers for the foreground objects
        Imgproc.threshold(dist, dist, 0.4, 1.0, Imgproc.THRESH_BINARY);
        // Dilate a bit the dist image
        Mat kernel1 = Mat.ones(3, 3, CvType.CV_8U);
        Imgproc.dilate(dist, dist, kernel1);
        Mat distDisplay2 = new Mat();
        dist.convertTo(distDisplay2, CvType.CV_8U);
        Core.multiply(distDisplay2, new Scalar(255), distDisplay2);
//        HighGui.imshow("Peaks", distDisplay2);
        // Create the CV_8U version of the distance image
        // It is needed for findContours()
        Mat dist_8u = new Mat();
        dist.convertTo(dist_8u, CvType.CV_8U);
        // Find total markers
        List<MatOfPoint> contours = new ArrayList<>();
        Mat hierarchy = new Mat();
        Imgproc.findContours(dist_8u, contours, hierarchy, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE);
        // Create the marker image for the watershed algorithm
        Mat markers = Mat.zeros(dist.size(), CvType.CV_32S);
        // Draw the foreground markers
        for (int i = 0; i < contours.size(); i++) {
            Imgproc.drawContours(markers, contours, i, new Scalar(i + 1), -1);
        }
        // Draw the background marker
        Mat markersScaled = new Mat();
        markers.convertTo(markersScaled, CvType.CV_32F);
        Core.normalize(markersScaled, markersScaled, 0.0, 255.0, Core.NORM_MINMAX);
        Imgproc.circle(markersScaled, new Point(5, 5), 3, new Scalar(255, 255, 255), -1);
        Mat markersDisplay = new Mat();
        markersScaled.convertTo(markersDisplay, CvType.CV_8U);
        Imgproc.circle(markers, new Point(5, 5), 3, new Scalar(255, 255, 255), -1);
        // Perform the watershed algorithm
        Imgproc.watershed(imgResult, markers);
        Mat mark = Mat.zeros(markers.size(), CvType.CV_8U);
        markers.convertTo(mark, CvType.CV_8UC1);
        Core.bitwise_not(mark, mark);
        // image looks like at that point
        // Generate random colors
        Random rng = new Random(12345);
        List<Scalar> colors = new ArrayList<>(contours.size());
        for (int i = 0; i < contours.size(); i++) {
            int b = rng.nextInt(256);
            int g = rng.nextInt(256);
            int r = rng.nextInt(256);
            colors.add(new Scalar(b, g, r));
        }
        // Create the result image
        Mat dst = Mat.zeros(markers.size(), CvType.CV_8UC3);
        byte[] dstData = new byte[(int) (dst.total() * dst.channels())];
        dst.get(0, 0, dstData);
        // Fill labeled objects with random colors
        int[] markersData = new int[(int) (markers.total() * markers.channels())];
        markers.get(0, 0, markersData);
        for (int i = 0; i < markers.rows(); i++) {
            for (int j = 0; j < markers.cols(); j++) {
                int index = markersData[i * markers.cols() + j];
                if (index > 0 && index <= contours.size()) {
                    dstData[(i * dst.cols() + j) * 3 + 0] = (byte) colors.get(index - 1).val[0];
                    dstData[(i * dst.cols() + j) * 3 + 1] = (byte) colors.get(index - 1).val[1];
                    dstData[(i * dst.cols() + j) * 3 + 2] = (byte) colors.get(index - 1).val[2];
                } else {
                    dstData[(i * dst.cols() + j) * 3 + 0] = 0;
                    dstData[(i * dst.cols() + j) * 3 + 1] = 0;
                    dstData[(i * dst.cols() + j) * 3 + 2] = 0;
                }
            }
        }
        dst.put(0, 0, dstData);
        // Visualize the final image
//        HighGui.imshow("Final Result", dst);
//        String path = "D:\\asddddd.png";
//        System.out.println("Done");
        marker = dst;
//        Imgcodecs.imwrite(path, marker); 

        Utility uti=new Utility();
        Vector<Integer> colorscale=new Vector<Integer>();
        BufferedImage bff=this.toBufferedImage(marker);
        ImageIO.write(bff, "png", new File("D:\\marker.png"));
        int[][] arys=uti.convert2intFormat2D(bff);
        for(int i=0;i<arys.length;i++){
             for(int j=0;j<arys[0].length;j++){
                 if(!colorscale.contains(arys[i][j]) && arys[i][j]!=0){
                     colorscale.add(arys[i][j]);
                 }
             }
         } 
        
        for(int i:colorscale){
            System.out.println("color is "+i);
            Vector<java.awt.Point> pts=new Vector<java.awt.Point>();
            for(int j=0;j<arys.length;j++){
                for(int k=0;k<arys[j].length;k++){
                    if(arys[j][k]==i){
                        pts.add(new java.awt.Point(j,k));
                    }
                }
            }
            Mask msk=new Mask(pts,pane,pane.wd.coloridx);
            masks.add(msk);
        }
        
        System.out.println("finished");
    }

    public int[][] getMarker() {
        BufferedImage img = this.toBufferedImage(marker);
        int[][] img_1 = this.convert2intArry(img, img.getWidth(), img.getHeight());
        return img_1;
    }

    public BufferedImage toBufferedImage(Mat matrix) {
        int type = BufferedImage.TYPE_BYTE_GRAY;
        if (matrix.channels() > 1) {
            type = BufferedImage.TYPE_3BYTE_BGR;
        }
        int bufferSize = matrix.channels() * matrix.cols() * matrix.rows();
        byte[] buffer = new byte[bufferSize];
        matrix.get(0, 0, buffer); // get all pixel from martix
        BufferedImage image = new BufferedImage(matrix.cols(), matrix.rows(), type);
        final byte[] targetPixels = ((DataBufferByte) image.getRaster().getDataBuffer()).getData();
        System.arraycopy(buffer, 0, targetPixels, 0, buffer.length);
        return image;
    }

    public int[][] convert2intArry(BufferedImage images, int row, int col) {
        int[][] image = new int[row][col];
        for (int i = 0; i < images.getWidth(); i++) {
            for (int j = 0; j < images.getHeight(); j++) {
                int color = images.getRGB(i, j);
                image[i][j] = color & 0xff;
            }
        }
        return image;
    }

    public Vector<Mask> getMasks() {
        return masks;
    }
    
}
