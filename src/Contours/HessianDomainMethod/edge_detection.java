/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Contours.HessianDomainMethod;

import java.awt.Graphics;
import java.awt.image.BufferedImage;
import java.awt.image.DataBufferByte;
import java.lang.reflect.Field;
import java.util.Vector;
import org.opencv.core.Core;
import org.opencv.core.CvType;
import org.opencv.core.Mat;
import org.opencv.core.Size;
import org.opencv.imgproc.Imgproc;

/**
 *
 * @author Andy C
 */
public class edge_detection {

    private int[][] pic_file;
    private double retreat_ratio;
    private int highthreshold, lowthreshold, segtime, gaussianArySize;
    private int[][] finalcontour;
    private Mat image;

    public edge_detection(int[][] pic_file, int highthreshold, int lowthreshold, double retreat_ratio, int segtime) throws Exception {
        this.pic_file = pic_file;
        this.highthreshold = highthreshold;
        this.lowthreshold = lowthreshold;
        this.retreat_ratio = retreat_ratio;
        this.segtime = segtime;
        this.gaussianArySize = gaussianArySize;
        this.finalcontour = new int[pic_file.length][pic_file[0].length];
        BufferedImage img = new BufferedImage(pic_file.length, pic_file[0].length, BufferedImage.TYPE_INT_RGB);
        Graphics c = img.getGraphics();
        for (int i = 0; i < pic_file.length; i++) {
            for (int j = 0; j < pic_file[i].length; j++) {
                int rgb = (int) pic_file[i][j] << 16 | (int) pic_file[i][j] << 8 | (int) pic_file[i][j];
                img.setRGB(i, j, rgb);
            }
        }

        this.image = this.bufferToMartix(img);
    }

    public void segpic() throws InterruptedException, Exception {
        int rowlength = pic_file.length;
        int rowlooptimes = (int) ((rowlength - (rowlength / segtime)) / ((rowlength / segtime) - (int) ((rowlength / segtime) * retreat_ratio)) + 1);
        int rowcroplen = (int) (rowlength / segtime);

        int collength = pic_file.length;
        int collooptimes = (int) ((collength - (collength / segtime)) / ((collength / segtime) - (int) ((collength / segtime) * retreat_ratio)) + 1);
        int colcroplen = (int) (collooptimes / segtime);
        for (int i = 0; i < rowlooptimes; i++) {
            int lastime_i = i;
            for (int j = 0; j < collooptimes; j++) {
                int lastime_j = j;
                if (i == 0 && j == 0) {
                    int[][] cropsl = this.getpart(pic_file, 0, rowcroplen, 0, colcroplen, rowcroplen, colcroplen, true);
                    int[][] enhenced = this.enhence(cropsl);
                    Mat part = this.intAry2Mat(enhenced);
                    Mat outpt=new Mat();
                    Imgproc.Canny(part, outpt, highthreshold, lowthreshold);
                    this.finalcontour = this.plugin(part, finalcontour, 0, rowcroplen, 0, colcroplen);
                    System.out.println("at 0");
                } else {
                    int startpos_i = (int) (lastime_i * rowcroplen - lastime_i * (rowcroplen * retreat_ratio));
                    int endpos_i = (int) (rowcroplen + (lastime_i * (rowcroplen - (rowcroplen * retreat_ratio))));
                    int startpos_j = (int) (lastime_j * colcroplen - lastime_j * (colcroplen * retreat_ratio));
                    int endpos_j = (int) (colcroplen + (lastime_j * (colcroplen - (colcroplen * retreat_ratio))));
                    int[][] cropsl = this.getpart(pic_file, startpos_i, endpos_i, startpos_j, endpos_j, rowcroplen, colcroplen, false);
                    int[][] enhenced = this.enhence(cropsl);
                    Mat part = this.intAry2Mat(enhenced);
                    Mat outpt=new Mat();
                    Imgproc.Canny(part, outpt, highthreshold, lowthreshold);
                    this.finalcontour = this.plugin(outpt, finalcontour, startpos_i, endpos_i, startpos_j, endpos_j);
                    System.out.println("at "+j);
                }

            }

        }

    }

    public int[][] getpart(int[][] grayscalepic, int start_sid_i, int end_sid_i, int start_sid_j, int end_sid_j, int rowlength, int collength, boolean first) {
        int[][] gray = new int[rowlength][collength];
        for (int i = start_sid_i; i < end_sid_i; i++) {
            for (int j = start_sid_j; j < end_sid_j; j++) {
                if (first == true) {
                    gray[i][j] = grayscalepic[i][j];
                } else {
                    gray[i - start_sid_i][j - start_sid_j] = grayscalepic[i][j];
                }
            }
        }
        return gray;
    }

    public int[][] plugin(Mat crtpart, int[][] target, int istart, int iend, int jstart, int jend) {
        BufferedImage patch = this.toBufferedImage(crtpart);
        int[][] part = this.convert2intArry(patch, target.length, target[0].length);
        for (int i = istart; i < iend; i++) {
            for (int j = jstart; j < jend; j++) {
                if (target[i][j] != 255) {
                    target[i][j] = part[i - istart][j - jstart];
                }
            }
        }
        return target;
    }

    public int[][] convert2intArry(BufferedImage images, int row, int col) {
        int[][] image = new int[row][col];
        for (int i = 0; i < images.getWidth(); i++) {
            for (int j = 0; j < images.getHeight(); j++) {
                int color= images.getRGB(i, j);
                image[i][j] =color & 0xff;
            }
        }
        return image;
    }

    public int[][] getfinalcontour() {
        return finalcontour;
    }
    
    public BufferedImage getfinalbufferedcontour(){
        BufferedImage img = new BufferedImage(pic_file.length, pic_file[0].length, BufferedImage.TYPE_INT_RGB);
        Graphics c = img.getGraphics();
        for (int i = 0; i < pic_file.length; i++) {
            for (int j = 0; j < pic_file[i].length; j++) {
                int rgb = (int) pic_file[i][j] << 16 | (int) pic_file[i][j] << 8 | (int) pic_file[i][j];
                img.setRGB(i, j, rgb);
            }
        }
        return img;
        
    }

    public int[][] convertfromVec(Vector<Vector> vec) {
        int[][] arr = new int[vec.size()][vec.get(0).size()];;
        for (int i = 0; i < arr.length; i++) {
            for (int j = 0; j < arr.length; j++) {
                arr[i][j] = (int) vec.get(i).get(j);
            }
        }
        return arr;
    }

    public int[][] enhence(int[][] img_target) {
        for (int i = 0; i < img_target.length; i++) {
            for (int j = 0; j < img_target[i].length; j++) {
                int a = img_target[i][j] * 2;
                if (a >= 255) {
                    img_target[i][j] = 255;
                } else {
                    img_target[i][j] = a;
                }
            }
        }
        return img_target;
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

    public static void loadOpenCV_Lib() throws Exception {
        // get the model
        String model = System.getProperty("sun.arch.data.model");
        // the path the .dll lib location
        String libraryPath = "D:\\opencv\\opencv\\build\\java\\";
        // check for if system is 64 or 32
        if (model.equals("64")) {
            libraryPath = "D:\\opencv\\opencv\\build\\java\\x64\\";
        }
        // set the path
        System.setProperty("java.library.path", libraryPath);
        Field sysPath = ClassLoader.class.getDeclaredField("sys_paths");
        sysPath.setAccessible(true);
        sysPath.set(null, null);
        // load the lib
        System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
    }

    public Mat bufferToMartix(BufferedImage image) throws Exception{
        loadOpenCV_Lib();
        image = convertTo3ByteBGRType(image);
        byte[] data = ((DataBufferByte) image.getRaster().getDataBuffer()).getData();
        Mat mat = new Mat(image.getHeight(), image.getWidth(), CvType.CV_8UC3);
        mat.put(0, 0, data);
        return mat;
    }
    
    private static BufferedImage convertTo3ByteBGRType(BufferedImage image) {
        BufferedImage convertedImage = new BufferedImage(image.getWidth(), image.getHeight(),
                BufferedImage.TYPE_3BYTE_BGR);
        convertedImage.getGraphics().drawImage(image, 0, 0, null);
        return convertedImage;
    }

    public Mat intAry2Mat(int[][] imag) throws Exception {
        BufferedImage img = new BufferedImage(imag.length, imag[0].length, BufferedImage.TYPE_INT_RGB);
        Graphics c = img.getGraphics();
        for (int i = 0; i < imag.length; i++) {
            for (int j = 0; j < imag[i].length; j++) {
                int rgb = imag[i][j] << 16 | imag[i][j] << 8 | imag[i][j];
                img.setRGB(i, j, rgb);
            }
        }
        Mat image = this.bufferToMartix(img);
        return image;
    }
}

