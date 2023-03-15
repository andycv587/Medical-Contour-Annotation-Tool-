/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.annotation;

import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.Point;
import java.awt.image.BufferedImage;
import java.awt.image.DataBufferByte;
import java.lang.reflect.Field;
import java.util.Vector;
import org.opencv.core.Core;
import org.opencv.core.CvType;
import org.opencv.core.Mat;

/**
 *
 * @author andy
 */
public class Utility {

    /*
    * Findline method
    * Status: Testing
    * find all coodrinates of a line
    * 
     */
    public Vector<Point> FindLine(int x1, int y1, int x2, int y2) {
        Vector<Point> list = new Vector<Point>();
        if (x1 == x2) {
            // Tangent = NaN
            int from = Math.min(y1, y2);
            int to = Math.max(y1, y2);
            for (int y = from; y <= to; y++) {
                list.add(new Point(x1, y));
            }
        } else {
            double slope = ((double) (y2 - y1)) / ((double) (x2 - x1));
            int step = (x2 > x1) ? 1 : -1;
            for (int x = x1; x != x2; x += step) {
                int y = (int) ((x - x1) * slope + y1);
                list.add(new Point(x, y));
            }
        }
        return list;
    }

    /*code of Getting the Path
        function: path creating based on folderPath and FileName
    status: full-developed
     */
    public String CreatingPath(String FolderPath, String FileName) {
        return FolderPath + "\\" + FileName;
    }

    /*
    * convert from bufferedImage array to 3d double array
    * Status: finished
     */
    public double[][][] convert2intArry(BufferedImage[] images) {
        double[][][] image = new double[images.length][images[0].getWidth()][images[0].getHeight()];
        for (int k = 0; k < image.length; k++) {
            for (int i = 0; i < image[k].length; i++) {
                for (int j = 0; j < image[k][i].length; j++) {
                    int color = images[k].getRGB(i, j);
                    image[k][i][j] = color & 0xff;
//                    System.out.print(" " + image[k][i][j]);
                }
//                System.out.println();
            }
//            System.out.println();

//            System.out.println("Another One");
        }
        return image;
    }
    
    public int[][][] convert2realintArry(BufferedImage[] images) {
        int[][][] image = new int[images.length][images[0].getWidth()][images[0].getHeight()];
        for (int k = 0; k < image.length; k++) {
            for (int i = 0; i < image[k].length; i++) {
                for (int j = 0; j < image[k][i].length; j++) {
                    int color = images[k].getRGB(i, j);
                    image[k][i][j] = color & 0xff;
//                    System.out.print(" " + image[k][i][j]);
                }
//                System.out.println();
            }
//            System.out.println();

//            System.out.println("Another One");
        }
        return image;
    }

    public int[][] convert2intFormat2D(BufferedImage images) {
        int[][] image = new int[images.getWidth()][images.getHeight()];
        for (int k = 0; k < image.length; k++) {
            for (int i = 0; i < image[k].length; i++) {
                int color = images.getRGB(k, i);
                image[k][i] = color & 0xff;

            }
        }
        return image;
    }


    /*plug v2's elements to v1, return v1*/
    public Vector extendVec(Vector v1, Vector v2) {
        for (int i = 0; i < v2.size(); i++) {
            v1.add(v2.get(i));
        }
        return v1;
    }

    public boolean issame(Vector<Point> v1, Vector<Point> v2) {
        boolean same = false;
        for (Point p : v1) {
            for (Point p2 : v2) {
                if (p.equals(p2)) {
                    same = true;
                }
            }
        }
        return same;
    }

    /*
    * add coma to the path
    * Status: finished
     */
    public String addcoma(String ori) {
        String str = ",]";
        String sub = ori.substring(0, ori.length() - 1);
        return sub + str;
    }

    /*
    * convert from 3d double array to 3d int array
    * Status: finished
     */
    public int[][][] cvtdb3d2int3d(double[][][] arr) {
        int[][][] a = new int[arr.length][arr[0].length][arr[0][0].length];
        for (int i = 0; i < a.length; i++) {
//            System.out.println("this is "+i+" slice");
            for (int j = 0; j < a[i].length; j++) {
                for (int k = 0; k < a[i][j].length; k++) {
                    a[i][j][k] = (int) arr[i][j][k];
                }
//                System.out.println();
            }
        }
        return a;
    }

    /*
    * convert from bufferedImage Vector to 3d int array
    * Status: finished
     */
    public int[][][] cvt2int3d(Vector<BufferedImage> imgs) {
        int[][][] arr = new int[imgs.size()][imgs.get(0).getWidth()][imgs.get(0).getHeight()];
        for (int a = 0; a < arr.length; a++) {
            BufferedImage crt = imgs.get(a);
            for (int i = 0; i < crt.getWidth(); i++) {
                for (int j = 0; j < crt.getHeight(); j++) {
                    int color = crt.getRGB(i, j);
                    arr[a][i][j] = color & 0xff;
                }
            }
        }
        return arr;
    }

    public BufferedImage resize(BufferedImage img, int col_n, int row_n) {
        Image im = img.getScaledInstance(col_n, row_n, Image.SCALE_SMOOTH);
        BufferedImage bimg = new BufferedImage(col_n, row_n, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2d = bimg.createGraphics();
        g2d.drawImage(im, 0, 0, null);
        return bimg;
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
//        String model = System.getProperty("sun.arch.data.model");
//        // the path the .dll lib location
//        String libraryPath = "D:\\opencv\\opencv\\build\\java\\";
//        // check for if system is 64 or 32
//        if (model.equals("64")) {
//            libraryPath = "D:\\opencv\\opencv\\build\\java\\x64\\";
//        }
//        // set the path
//        System.setProperty("java.library.path", libraryPath);
//        Field sysPath = ClassLoader.class.getDeclaredField("sys_paths");
//        sysPath.setAccessible(true);
//        sysPath.set(null, null);
        // load the lib
        System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
    }

    public Mat bufferToMartix(BufferedImage image) throws Exception {
        loadOpenCV_Lib();
        image = convertTo3ByteBGRType(image);
        byte[] data = ((DataBufferByte) image.getRaster().getDataBuffer()).getData();
        Mat mat = new Mat(image.getHeight(), image.getWidth(), CvType.CV_8UC3);
        mat.put(0, 0, data);
        return mat;
    }

    public static BufferedImage convertTo3ByteBGRType(BufferedImage image) {
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
