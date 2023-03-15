/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Main.java to edit this template
 */
package Contours.experiments;

import Contours.annotation.nifti;
import java.awt.Graphics;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.Vector;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.imageio.ImageIO;
import org.opencv.core.Mat;

/**
 *
 * @author andy
 */
public class JavaYieldExp {

    public static void main(String[] args) {
        Vector<double[][]> v1 = new Vector<double[][]>();
        Vector<double[][]> v2 = new Vector<double[][]>();
        Vector<double[][]> v3 = new Vector<double[][]>();
        Vector<double[][]> v4 = new Vector<double[][]>();
        Vector<double[][]> v5 = new Vector<double[][]>();
//        Vector<double[][]> vall=new Vector<double[][]>();
        nifti nif = new nifti("D:\\Conference\\2023SPIE\\Experiment_Files\\nifti\\la_003.nii.gz");
        double[][][] imgarr = nif.getVolume();
        for (int i = 0; i < imgarr.length; i++) {
            if (i % 5 == 0) {
                v1.add(imgarr[i]);
            } else if (i % 5 == 1) {
                v2.add(imgarr[i]);
            } else if (i % 5 == 2) {
                v3.add(imgarr[i]);
            } else if (i % 5 == 3) {
                v4.add(imgarr[i]);
            } else if (i % 5 == 4) {
                v5.add(imgarr[i]);
            }
//            vall.add(imgarr[i]);
        }
        
//        for (int i = 0; i < vall.size(); i++) {
//            try {
//                
//                File f = new File("D:\\experimentimg\\imagestream_" + i + ".png");
//                ImageIO.write(doubleAry2buff(vall.get(i)), "png", f);
//            } catch (Exception ex) {
//                Logger.getLogger(imagereadingstream.class.getName()).log(Level.SEVERE, null, ex);
//            }
//        }

        
        
        imagereadingstream thread1 = new imagereadingstream(v1, 1);
        imagereadingstream thread2 = new imagereadingstream(v2, 2);
        imagereadingstream thread3 = new imagereadingstream(v3, 3); 
        imagereadingstream thread4 = new imagereadingstream(v4, 4);
        imagereadingstream thread5 = new imagereadingstream(v5, 5);
        thread1.start();
        thread2.start();
        thread3.start();
        thread4.start();
        thread5.start();

    }
    
    public static BufferedImage doubleAry2buff(double[][] imag) throws Exception {
        BufferedImage img = new BufferedImage(imag.length, imag[0].length, BufferedImage.TYPE_INT_RGB);
        Graphics c = img.getGraphics();
        for (int i = 0; i < imag.length; i++) {
            for (int j = 0; j < imag[i].length; j++) {
                int rgb = (int) imag[i][j] << 16 | (int) imag[i][j] << 8 | (int) imag[i][j];
                img.setRGB(i, j, rgb);
            }
        } 
        return img;
    }

}

class imagereadingstream extends Thread {

    private Vector<double[][]> img;
    private Vector<BufferedImage> imgs;
    private int threadnum;

    public BufferedImage doubleAry2buff(double[][] imag) throws Exception {
        BufferedImage img = new BufferedImage(imag.length, imag[0].length, BufferedImage.TYPE_INT_RGB);
        Graphics c = img.getGraphics();
        for (int i = 0; i < imag.length; i++) {
            for (int j = 0; j < imag[i].length; j++) {
                int rgb = (int) imag[i][j] << 16 | (int) imag[i][j] << 8 | (int) imag[i][j];
                img.setRGB(i, j, rgb);
            }
        }
        return img;
    }

    public void run() {
        for (int i = 0; i < img.size(); i++) {
            try {
                sleep(1);
                imgs.add(this.doubleAry2buff(img.get(i)));
                File f = new File("D:\\experimentimg\\imagestream_" + threadnum + "_" + i + ".png");
                ImageIO.write(imgs.get(i), "png", f);
            } catch (Exception ex) {
                Logger.getLogger(imagereadingstream.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
    }

    public imagereadingstream(Vector<double[][]> img, int threadnum) {
        this.img = img;
        this.imgs = new Vector<BufferedImage>();
        this.threadnum = threadnum;
    }

}
