/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Contours.HessianDomainMethod;
import java.awt.Graphics;
import java.awt.image.BufferedImage;

/**
 *
 * @author Andy C
 */
public class MergeChannels {
    private BufferedImage ch1, ch2;
    private int[][] intch1, intch2;
    private double ratioch1, ratioch2;
    
    public MergeChannels(BufferedImage ch1, BufferedImage ch2, double ratioch1, double ratioch2){
        this.ch1=ch1;
        this.ch2=ch2;
        this.ratioch1=ratioch1;
        this.ratioch2=ratioch2;
        intch1=this.convert2intArry(ch1);
        intch2=this.convert2intArry(ch2);
    }
    
    public BufferedImage merge(){
        double[][] merged=new double[intch1.length][intch2.length];
        for(int i=0;i<merged.length;i++){
            for (int j=0;j<merged.length;j++){
                merged[i][j]=intch1[i][j]*ratioch1+intch2[i][j]*ratioch2;
            }
        }
        int[][] newimg=this.normalization(merged, 255, 0);
        
        return this.int2d2bfi(newimg);
    }
    
    public int[][] normalization(double[][] img,int max, int min){
        int[][] newimg=new int[img.length][img[0].length];
        double[] extremas=extrema(img);
        for(int i=0;i<img.length;i++){
            for(int j=0;j<img[i].length;j++){
                double a=(max - min) / (extremas[0] - extremas[1]);
                double b = max - a * extremas[0];
                newimg[i][j] =(int) (a * img[i][j] + b);
            }
        }
        return newimg;
    }
    
    public double[] extrema(double[][] ary){
        double extremas[]={ary[0][0],ary[0][0]};
        for(int i=0;i<ary.length;i++){
            for(int j=0;j<ary[0].length;j++){
                if(ary[i][j]>extremas[0])
                    extremas[0]=ary[i][j];
                
                if(ary[i][j]<extremas[1])
                    extremas[1]=ary[i][j];
            }
        }
        return extremas;
    }
    
    public int[][] convert2intArry(BufferedImage images) {
        int[][] image = new int[images.getWidth()][images.getHeight()];
        for (int i = 0; i < images.getWidth(); i++) {
            for (int j = 0; j < images.getHeight(); j++) {
                int color= images.getRGB(i, j);
                image[i][j] =color & 0xff;
            }
        }
        return image;
    }

    public BufferedImage int2d2bfi(int[][] pic_file) {
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
    
}
