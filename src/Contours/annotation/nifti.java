/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Contours.annotation;

import java.awt.Graphics;
import java.awt.image.BufferedImage;
import java.io.IOException;
import Contours.niftijio.*;

/**
 *
 * @author Andy C
 */
public class nifti {

    private double[][][] volume;
    private String address;
    private double max,min;    
    private NiftiVolume vol;

    public nifti(String address) {
        this.address=address;
        try {
            this.vol=NiftiVolume.read(address);            

            double[][][][] dat=vol.data.toArray();
//            System.out.println("dimension for dat="+dat.length+" "+dat[0].length+" "+dat[0][0].length+" "+dat[0][0][0].length);
            this.volume = this.lowerdimensions(dat);
//            System.out.println("dimension for volume="+volume.length+" "+volume[0].length+" "+volume[0][0].length);
        this.max=this.getMax();
        this.min=this.getMax();
            System.out.println();
        } catch (IOException e) {
            System.err.println("error: " + e.getMessage());
        }
    }
    
    public nifti(double[][][][] dat){
        this.vol=new NiftiVolume(dat);
        this.volume=this.lowerdimensions(dat);
        this.max=this.getMax();
        this.min=this.getMin();
    }

    public double[][][] getVolume() {
        return volume;
    }

    public BufferedImage[] toBufferedImageArr(double max, double min) throws IOException {
        BufferedImage[] imgset = new BufferedImage[volume.length];
        niftishowing num= new niftishowing(NiftiVolume.read(address));
        int[][][] vol=num.normalization(volume, max, min);
        for (int slice=0;slice<vol.length;slice++) {
            int[][] arr=vol[slice];
            BufferedImage img = new BufferedImage(arr.length, arr[0].length, BufferedImage.TYPE_INT_RGB);
            Graphics c = img.getGraphics();
            for(int i=0;i<arr.length;i++){
                for(int j=0;j<arr[i].length;j++){
                    int rgb = (int)arr[i][j]<<16 | (int)arr[i][j] << 8 | (int)arr[i][j];
                    img.setRGB(i, j, rgb);
                }
            }
            imgset[slice]=img;
        }
        return imgset;
    }
    
    public double[][][] lowerdimensions(double[][][][] data){
        double[][][] newdat=new double[data.length][data[0].length][data[0][0].length];
        //first loop
        for(int i=0;i<data.length;i++){
            for(int j=0;j<data[i].length;j++){
                for(int k=0;k<data[i][j].length;k++){
                    newdat[i][j][k]=data[i][j][k][0];
                }
            }
        }
        
        double[][][] res=new double[newdat[0][0].length][newdat[0].length][newdat.length];
        for(int i=0;i<res.length;i++){
            for(int j=0;j<res[i].length;j++){
                for(int k=0;k<res[i][j].length;k++){
                    res[i][j][k]=newdat[k][j][i];
                }
            }
        }
        return res;
    }
    
    public double getMax(){
        double max=volume[0][0][0];
        for(double[][] row:volume){
            for(double[] col:row){
                for(double num:col){
                    if(num>max){
                        max=num;
                    }
                }
            }
        }
        return max;
    }
    
    public double getMin(){
        double min=volume[0][0][0];
        for(double[][] row:volume){
            for(double[] col:row){
                for(double num:col){
                    if(num<min){
                        min=num;
                    }
                }
            }
        }
        return min;
    }

}

class niftishowing {

    private final NiftiVolume vol;
    private double max,min;
    private int pagenum;
    

    public niftishowing(NiftiVolume vol) {
        this.vol = vol;
    }
    
    public int[][][] normalization(double[][][] data, double max, double min) {
        int[][][] output = new int[data.length][data[0].length][data[0][0].length];
        double range = max - min;
        for (int i = 0; i < data.length; i++) {
            for (int j = 0; j < data[i].length; j++) {
                for (int k = 0; k < data[i][j].length; k++) {
                    double current = data[i][j][k];
                    if (current > min && current < max) {
                        int pix = (int) (current / range * 255);
                        output[i][j][k] = pix;
                    }else if(current<=min){
                        output[i][j][k] = 0;
                    }else{
                        output[i][j][k] = 255;
                    }

                }
            }
        }
        return output;
    }

    public double max(double[][][] array) {
        double max = array[0][0][0];
        for (double[][] scd : array) {
            for (double[] trd : scd) {
                for (double fth : trd) {
                    if (fth > max) {
                        max = fth;
                    }
                }
            }
        }
        this.max=max;
        return max;
    }

    public double min(double[][][] array) {
        double min = array[0][0][0];
        for (double[][] scd : array) {
            for (double[] trd : scd) {
                for (double fth : trd) {
                    if (fth < min) {
                        min = fth;
                    }
                }
            }
        }
        this.min=min;
        return min;
    }

    public double[][] int2d2double2d(int[][] ary) {
        double[][] result = new double[ary.length][ary[0].length];
        for (int i = 0; i < ary.length; i++) {
            for (int j = 0; j < ary[i].length; j++) {
                result[i][j] = ary[i][j];
            }
        }

        return result;
    }

}
