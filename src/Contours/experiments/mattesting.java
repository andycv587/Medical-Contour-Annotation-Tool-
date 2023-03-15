/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.experiments;
import org.opencv.core.*;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.highgui.HighGui;
import org.opencv.core.CvType;


/**
 *
 * @author andy
 */
public class mattesting {
    public static void main(String[] args){
        System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
        Mat mat=Imgcodecs.imread("D:\\Conference\\2022SPIE\\Results\\exp_folder\\colon\\oripng\\1-30.png");
//        HighGui.imshow("star", mat);
//        HighGui.waitKey();
        double[] f=mat.get(100,100);
        System.out.println(f[1]);
        System.out.println(f[2]);
        
        System.out.println(f[0]);
        double d[]={1,2,3,5};
        a(1,2,3,4);
    }
    
    public static void a(double... anyw){
        System.out.print(anyw[0]);
    }
}
