/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Main.java to edit this template
 */
package Contours.experiments;

import Contours.annotation.Utility;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Collections;
import java.util.Vector;
import org.opencv.core.Core;
import org.opencv.core.CvType;
import org.opencv.core.Mat;
import org.opencv.core.Rect;
import org.opencv.highgui.HighGui;
import static org.opencv.imgcodecs.Imgcodecs.imread;
import org.opencv.imgproc.*;
import org.opencv.core.Point;
import org.opencv.core.Scalar;
import org.opencv.core.MatOfPoint;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import static org.opencv.imgproc.Imgproc.Sobel;
import static org.opencv.imgproc.Imgproc.cvtColor;

/**
 *
 * @author tucke
 */
public class Levelset {

    public int m_iterNum;      //迭代次数  
    public float m_lambda1;    //全局项系数  
    public float m_nu;     //长度约束系数ν  
    public float m_mu;     //惩罚项系数μ  
    public float m_timestep;   //演化步长δt  
    public float m_epsilon;    //规则化参数ε  

    //过程数据  
    public Mat m_mImage;       //源图像  

    public int m_iCol;     //图像宽度  
    public int m_iRow;     //图像高度  
    public int m_depth;        //水平集数据深度  
    public float m_FGValue;    //前景值  
    public float m_BKValue;    //背景值  
    public Mat m_mPhi;     //水平集：φ  
    public Mat showIMG;

    protected Mat m_mDirac;       //狄拉克处理后水平集：δ（φ）  
    protected Mat m_mHeaviside;   //海氏函数处理后水平集：Н（φ）  
    protected Mat m_mCurv;        //水平集曲率κ=div(▽φ/|▽φ|)  
    protected Mat m_mK;       //惩罚项卷积核  
    protected Mat m_mPenalize;    //惩罚项中的▽<sup>2</sup>φ  

    public Levelset() {
        m_iterNum = 50;
        m_lambda1 = 13;
        m_nu = (float) (0.001 * 255 * 255);
        m_mu = (float) 1.0;
        m_timestep = (float) 0.1;
        m_epsilon = (float) 1.0;
    }

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) throws IOException {
        System.loadLibrary(Core.NATIVE_LIBRARY_NAME);
        Mat img = imread("D:\\Conference\\2022SPIE\\Results\\exp_folder\\colon\\oripng\\1-30.png");
        HighGui.imshow("orig", img);
        Rect rec = new Rect(0, 0, img.cols(), img.rows());
        Levelset ls = new Levelset();
        ls.initializePhi(img, 20, rec);
        ls.EVolution();
//        HighGui.imshow("Level Set后图像", showIMG);
//        HighGui.imshow("star", mat);
//        HighGui.waitKey();


    }

    public void initializePhi(Mat img, int iterNum, Rect boxPhi) throws IOException {
        m_iterNum = iterNum;
        m_iCol = img.cols();
        m_iRow = img.rows();
        m_depth = CvType.CV_32FC1;

        m_mPhi = Mat.zeros(m_iRow, m_iCol, m_depth);
//        this.saveArrayToFile(m_mPhi,"D:\\m_mPhi_zeros.txt");
        m_mDirac = Mat.zeros(m_iRow, m_iCol, m_depth);
        m_mHeaviside = Mat.zeros(m_iRow, m_iCol, m_depth);
        m_mCurv = new Mat(m_iRow, m_iCol, m_depth);
        m_mPenalize = new Mat(m_iRow, m_iCol, m_depth);
        showIMG= new Mat(m_iRow, m_iCol, m_depth);
        
        m_mK = new Mat(3, 3, CvType.CV_32FC1);
        int row = 0, col = 0;
        img.put(row, col, 0, -1, 0, -1, 5, -1, 0, -1, 0);
        int c;
        c = 2;

        for (int i = 0; i < m_iRow; i++) {
            for (int j = 0; j < m_iCol; j++) {
                if (i < boxPhi.y && i > boxPhi.y + boxPhi.height && j < boxPhi.x && j > boxPhi.x + boxPhi.width) {
                    m_mPhi.put(i, j, -c);
                } else {
                    m_mPhi.put(i, j, c);
                }
            }
        }
//       this.saveArrayToFile(m_mPhi,"D:\\m_mPhi_afterc.txt");

    }

    public void EVolution() throws IOException {
        float fCurv;
        float fDirac;
        float fPenalize;
        float fImgValue;

        for (int it = 0; it < m_iterNum; it++) {
            Dirac();
            Curvature();
            BinaryFit();
            Imgproc.filter2D(m_mPhi, m_mPenalize, m_depth, m_mK,new Point(1,1));
            for (int i = 0; i < m_iRow; i++) {
                for (int j = 0; j < m_iCol; j++) {
                    fCurv = (float) m_mCurv.get(i, j)[0];
                    fDirac = (float) m_mDirac.get(i, j)[0];
                    fPenalize = (float) m_mPenalize.get(i, j)[0];
                    fImgValue = (float) m_mImage.get(i, j)[0];

                    float lengthTerm = m_nu * fDirac * fCurv;
                    float penalizeTerm = m_mu * (fPenalize - fCurv);
                    float areaTerm = fDirac * m_lambda1 * (-((fImgValue - m_FGValue) * (fImgValue - m_FGValue)) + ((fImgValue - m_BKValue) * (fImgValue - m_BKValue)));
                    float sum=(float)(m_mPhi.get(i, j)[0] + m_timestep * (lengthTerm + penalizeTerm + areaTerm));
//                    System.out.print((double)sum+" ");
                    m_mPhi.put(i, j,sum );
                }
//                System.out.println();
            }

            cvtColor(m_mImage, showIMG, Imgproc.COLOR_GRAY2BGR);
            Mat Mask = m_mPhi;   //findContours的输入是二值图像  
            Imgproc.dilate(Mask, Mask, new Mat(), new Point(-1, -1), 3);
            Imgproc.erode(Mask, Mask, new Mat(), new Point(-1, -1), 3);
            Vector<MatOfPoint> contours = new Vector<MatOfPoint>();
            
            Utility util=new Utility();
//            BufferedImage bfi=util.toBufferedImage(Mask);
//            int[][] imgs=util.convert2intFormat2D(bfi);
//            for(int i=0;i<imgs.length;i++){
//                for(int j=0;j<imgs[i].length;j++){
//                    System.out.print(imgs[i][j]+" ");
//                }
//                System.out.println();
//            }
            
            Imgcodecs imageCodecs = new Imgcodecs();  
            imageCodecs.imwrite("D:\\pics\\"+it+".png", m_mImage);
            
//            Imgproc.findContours(Mask, contours, Mask, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_NONE);
//            Imgproc.drawContours(showIMG, contours, -1, new Scalar(255, 0, 0), 2);
//            HighGui.namedWindow("Level Set后图像");
//            HighGui.imshow("Level Set后图像", showIMG);
//            HighGui.waitKey(1);

        }
    }

    protected void Dirac() {
        float k1 = (float) (m_epsilon / Math.PI);
        float k2 = (float) (m_epsilon * m_epsilon);
        for (int i = 0; i < m_iRow; i++) {
            for (int j = 0; j < m_iCol; j++) {
                double[] prtPhi_1 = m_mPhi.get(i, j);
                float b = (float) (k1 / (k2 + prtPhi_1[0] * prtPhi_1[0]));
                m_mDirac.put(i, j, b);
            }
        }

    }

    protected void Heaviside() {
        float k3 = (float) (2 / Math.PI);
        for (int i = 0; i < m_iRow; i++) {
            for (int j = 0; j < m_iCol; j++) {
                float phiV = (float) m_mPhi.get(i, j)[0];
                float v = (float) m_mHeaviside.get(i, j)[0];
                m_mHeaviside.put(i, j, (float) (0.5 * (1 + k3 * Math.atan(phiV / m_epsilon))));
            }
        }
    }

    protected void Curvature() throws IOException {
        Mat dx = new Mat(m_iRow, m_iCol, m_depth), dy = new Mat(m_iRow, m_iCol, m_depth);
        Sobel(m_mPhi, dx, m_mPhi.depth(), 1, 0, 1);
        Sobel(m_mPhi, dy, m_mPhi.depth(), 0, 1, 1);
        for (int i = 0; i < m_iRow; i++) {
            for (int j = 0; j < m_iCol; j++) {
                double prtdx = dx.get(i, j)[0];
                double prtdy = dy.get(i, j)[0];
                double val = Math.sqrt(prtdx * prtdx + prtdy * prtdy + 1e-10);
                dx.put(i, j, prtdx / val);
                dy.put(i, j, prtdy / val);
            }
        }

        Mat ddx = new Mat(m_iRow, m_iCol, m_depth), ddy = new Mat(m_iRow, m_iCol, m_depth);
        Sobel(dx, ddy, m_mPhi.depth(), 0, 1, 1);
        Sobel(dy, ddx, m_mPhi.depth(), 1, 0, 1);
//        this.saveArrayToFile(ddx,"D:\\ddx.txt");
//        this.saveArrayToFile(ddy,"D:\\ddy.txt");
        Core.add(ddx, ddy, m_mCurv);
    }

    protected void BinaryFit() {
        Heaviside();
        m_mImage = new Mat(m_iRow, m_iCol, m_depth);

        float sumFG = 0;
        float sumBK = 0;
        float sumH = 0;

        Mat temp = m_mHeaviside;
        Mat temp2 = m_mImage;
        float fHeaviside;
        float fFHeaviside;
        float fImgValue;
        for (int i = 1; i < m_iRow; i++) {
            for (int j = 1; j < m_iCol; j++) {
                fImgValue = (float) m_mImage.get(i, j)[0];
                fHeaviside = (float) m_mHeaviside.get(i, j)[0];
                fFHeaviside = 1 - fHeaviside;

                sumFG += fImgValue * fHeaviside;
                sumBK += fImgValue * fFHeaviside;
                sumH += fHeaviside;
            }
        }
        m_FGValue = (float) (sumFG / (sumH + 1e-10));
        m_BKValue = (float) (sumBK / (m_iRow * m_iCol - sumH + 1e-10));
    }


    private void saveArrayToFile(Mat img,String fileName) throws IOException {
        double[][] array = new double[img.rows()][img.cols()];
        for (int i = 0; i < array.length; i++) {
            for (int j = 0; j < array[i].length; j++) {
                array[i][j] = img.get(i, j)[0];
            }
        }
        int a=0;
        String str="";
//        for (int i = 0; i < array.length; i++) {
//            for (int j = 0; j < array[i].length; j++) {
//                str=str+array[i][j]+" ";
//                a+=1;
//                System.out.println(a);
//            }
//            str+="\n";
//        }
        
        Files.write( // write to file
                Paths.get(fileName), // get path from file
                Collections.singleton(str), // transform array to collection using singleton
                Charset.forName("UTF-8") // formatting
        );
    }
}
