/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Contours.HessianDomainMethod;

import Contours.HessianDomainMethod.*;
import java.util.Vector;
import Jama.Matrix;
import java.awt.Graphics;
import java.awt.image.BufferedImage;

/**
 *
 * @author Andy C
 */
public class Hessian_Deriche_3D_modified {

    private Vector<double[][][]> filter = new Vector();
    private double[][][] rawimg;
    private double[][] grayscale;
    private int winradius, mappingpower, nullCT;
    private double alpha;

    public Hessian_Deriche_3D_modified(double[][] grayscale, int winradius, double alpha, int mappingpower, int nullCT) {
        this.grayscale = grayscale;
        this.winradius = winradius;
        this.alpha = alpha;
        this.mappingpower = mappingpower;
        this.nullCT = nullCT;
        rawimg = todb3d(grayscale);
    }

    public int[][] gaussianblur(int[][] data, double sigma, int dims) {

        return data;
    }

    public void Hessian_deriche_3D() {
        int rsz[] = {rawimg.length, rawimg[0].length, rawimg[0][0].length};
        int dim = rsz.length;
        if (dim == 3) {
            int rq = rsz[0];
            int rm = rsz[1];
            int rn = rsz[2];

            double[][][] lambda_mag = this.Times(this.ones(rq,rm,rn), nullCT);
            double[][][] lambda_azimuth = this.Times(this.ones(rq,rm,rn), nullCT);
            double[][][] lambda_polarangle = this.Times(this.ones(rq,rm,rn), nullCT);
            double[][][] lambda_sum = this.Times(this.ones(rq,rm,rn), nullCT);
            double[][][] lambda_product = this.Times(this.ones(rq,rm,rn), nullCT);

            double[][][] grawimage = todb3d(grayscale);
            derichefilter_mod dm = new derichefilter_mod();
            Vector<double[][][]> filters = dm.derichefilters_modified(alpha, winradius, dim);
            double[][][] fxx = filters.get(4);
            double[][][] fyy = filters.get(5);
            double[][][] fzz = filters.get(6);
            double[][][] fxy = filters.get(7);
            double[][][] fxz = filters.get(8);
            double[][][] fyz = filters.get(9);
            
            double[][][] ixx = this.conv3d(grawimage, fxx);
            double[][][] ixy = this.conv3d(grawimage, fxy);
            double[][][] ixz = this.conv3d(grawimage, fxz);
            double[][][] iyy = this.conv3d(grawimage, fyy);
            double[][][] iyz = this.conv3d(grawimage, fyz);
            double[][][] izz = this.conv3d(grawimage, fzz);

            for (int z = 0; z < rq; z++) {
                for (int x = 0; x < rm; x++) {
                    for (int y = 0; y < rn; y++) {
                        double cixx = ixx[z][x][y];
                        double cixy = ixy[z][x][y];
                        double cixz = ixz[z][x][y];
                        double ciyy = iyy[z][x][y];
                        double ciyz = iyz[z][x][y];
                        double cizz = izz[z][x][y];

                        double[][] curh = {{cixx, cixy, cixz}, {cixy, ciyy, ciyz}, {cixz, ciyz, cizz}};
                        Matrix mat = new Matrix(curh);
                        Matrix res = mat.eig().getD();
                        double[][] cd = res.getArray();

                        double curmag = Math.pow(cd[0][0] * cd[0][0] + cd[0][1] * cd[0][1] + cd[0][2] * cd[0][2], .5);
                        lambda_mag[z][x][y] = this.metricmapping(curmag, mappingpower);
                        
                        double curvec[] = {cd[0][0], cd[0][1], cd[0][2]};
                        
                        double cur_lbaz = this.angle(curvec)[0];
                        double cur_lbpolar = this.angle(curvec)[1];

                        lambda_azimuth[z][x][y] = cur_lbaz;
                        lambda_polarangle[z][x][y] = cur_lbpolar;

                        lambda_sum[z][x][y] = this.metricmapping(Math.abs(cixx + ciyy + cizz), mappingpower);
                        Matrix det = new Matrix(curh);

                        lambda_product[z][x][y] = this.metricmapping(Math.abs(det.det()), mappingpower);

                    }
                }
            }
            filter.add(lambda_mag);
            filter.add(lambda_azimuth);
            filter.add(lambda_polarangle);
            filter.add(lambda_sum);
            filter.add(lambda_product);
        }
        
    }

    public double[][][] todb3d(double[][] grayscale) {
        double[][][] db = new double[grayscale[0].length][grayscale.length][3];
        for (int i = 0; i < db.length; i++) {
            for (int j = 0; j < db[i].length; j++) {
                db[i][j][0] = grayscale[j][i];
                db[i][j][1] = grayscale[j][i];
                db[i][j][2] = grayscale[j][i];
            }
        }
        return db;
    }

    public double metricmapping(double mval, double mappingpower) {
        double val = 0;
        if (mval >= 0) {
            val = Math.pow(mval, 1 / mappingpower);
        } else {
            val = -(Math.pow(mval, 1 / mappingpower));
        }
        return val;
    }

    public double[] angle(double[] v) {
        double[] ans = new double[2];
        if (v.length != 0 && v.length == 3) {
            double x = v[0];
            double y = v[1];
            double z = v[2];
            double theta = Math.atan(y / (x+0.0000000001));

            double azimuth = 0;
            if (Math.abs(x) <= 0.0000000001 && Math.abs(y) <= 0.0000000001) {
                azimuth = 0;
            } else {
                if (x >= 0 && y >= 0) {
                    azimuth = theta;
                } else {
                    if (x < 0 && y >= 0) {
                        azimuth = Math.PI - theta;
                    } else {
                        if (x < 0 && y < 0) {
                            azimuth = Math.PI + theta;
                        } else {
                            azimuth = 2 * Math.PI - Math.abs(theta);
                        }
                    }
                }
            }

            double polarangle = 0;
            if (Math.abs(x) <= 0.0000000001 && Math.abs(y) <= 0.0000000001 && Math.abs(z) <= 0.0000000001) {
                polarangle = 0;
            } else {
                polarangle = Math.atan(z / Math.sqrt(x * x + y * y + 0.0000000001) + Math.PI / 2);
            }

            ans[0] = azimuth;
            ans[1] = polarangle;
        }
        return ans;
    }

    public double[][][] ones(int row, int col, int slide) {
        double[][][] arr = new double[row][col][slide];
        for (int i = 0; i < row; i++) {
            for (int j = 0; j < col; j++) {
                for (int k = 0; k < slide; k++) {
                    arr[i][j][k] = 1;
                }
            }
        }
        return arr;
    }

    public double[][][] Times(double[][][] arr, int num) {
        for (int i = 0; i < arr.length; i++) {
            for (int j = 0; j < arr[i].length; j++) {
                for (int k = 0; k < arr[i][j].length; k++) {
                    arr[i][j][k] = arr[i][j][k] * num;
                }
            }
        }
        return arr;
    }

    //3d conv 3*3*3 kernal
    public double[][][] conv3d(double[][][] data, double[][][] kernal) {
        double[][][] convolved = new double[data.length][data[0].length][data[0][0].length];
        double[][][] exped = this.expand(data);

        //3d
        //move back
        for (int slice = 0; slice < convolved.length; slice++) {
            //move down
            for (int row = 0; row < convolved[slice].length; row++) {
                //move right
                for (int col = 0; col < convolved[slice][row].length; col++) {
                    double d000 = kernal[0][0][0] * exped[slice][row][col];
                    double d001 = kernal[0][0][1] * exped[slice][row][col + 1];
                    double d002 = kernal[0][0][2] * exped[slice][row][col + 2];
                    double d010 = kernal[0][1][0] * exped[slice][row + 1][col];
                    double d011 = kernal[0][1][1] * exped[slice][row + 1][col + 1];
                    double d012 = kernal[0][1][2] * exped[slice][row + 1][col + 2];
                    double d020 = kernal[0][2][0] * exped[slice][row + 2][col];
                    double d021 = kernal[0][2][1] * exped[slice][row + 2][col + 1];
                    double d022 = kernal[0][2][2] * exped[slice][row + 2][col + 2];
                    double d100 = kernal[1][0][0] * exped[slice + 1][row][col];
                    double d101 = kernal[1][0][1] * exped[slice + 1][row][col + 1];
                    double d102 = kernal[1][0][2] * exped[slice + 1][row][col + 2];
                    double d110 = kernal[1][1][0] * exped[slice + 1][row + 1][col];
                    double d111 = kernal[1][1][1] * exped[slice + 1][row + 1][col + 1];
                    double d112 = kernal[1][1][2] * exped[slice + 1][row + 1][col + 2];
                    double d120 = kernal[1][2][0] * exped[slice + 1][row + 2][col];
                    double d121 = kernal[1][2][1] * exped[slice + 1][row + 2][col + 1];
                    double d122 = kernal[1][2][2] * exped[slice + 1][row + 2][col + 2];
                    double d200 = kernal[2][0][0] * exped[slice + 2][row][col];
                    double d201 = kernal[2][0][1] * exped[slice + 2][row][col + 1];
                    double d202 = kernal[2][0][2] * exped[slice + 2][row][col + 2];
                    double d210 = kernal[2][1][0] * exped[slice + 2][row + 1][col];
                    double d211 = kernal[2][1][1] * exped[slice + 2][row + 1][col + 1];
                    double d212 = kernal[2][1][2] * exped[slice + 2][row + 1][col + 2];
                    double d220 = kernal[2][2][0] * exped[slice + 2][row + 2][col];
                    double d221 = kernal[2][2][1] * exped[slice + 2][row + 2][col + 1];
                    double d222 = kernal[2][2][2] * exped[slice + 2][row + 2][col + 2];
                    double max = d000 + d001 + d002 + d010 + d011 + d012 + d020 + d021 + d022 + d100 + d101 + d102 + d110 + d111 + d112 + d120 + d121 + d122 + d200 + d201 + d202 + d210 + d211 + d212 + d220 + d221 + d222;
                    convolved[slice][row][col] = max;
                }
            }
        }

        return convolved;
    }

    public double[][][] expand(double[][][] data) {
        double[][][] newdata = new double[data.length + 2][data[0].length + 2][data[0][0].length + 2];
        for (int slice = 0; slice < data.length; slice++) {
            for (int row = 0; row < data[slice].length; row++) {
                for (int col = 0; col < data[slice][row].length; col++) {
                    //assign the first and second of newdata
                    if (slice == 0) {
                        for (int i = 0; i < 2; i++) {
                            //top left front
                            if (row == 0 && col == 0) {
                                newdata[i][row][col] = data[slice][row][col];
                                newdata[i][row][col + 1] = data[slice][row][col];
                                newdata[i][row + 1][col] = data[slice][row][col];
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                //top right front
                            } else if (row == 0 && col == data[slice][row].length - 1) {
                                newdata[i][row][col + 1] = data[slice][row][col];
                                newdata[i][row][col + 2] = data[slice][row][col];
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                newdata[i][row + 1][col + 2] = data[slice][row][col];
                                //bot left front
                            } else if (row == data[slice].length - 1 && col == 0) {
                                newdata[i][row + 1][col] = data[slice][row][col];
                                newdata[i][row + 2][col] = data[slice][row][col];
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                newdata[i][row + 2][col + 1] = data[slice][row][col];
                                //bot right front
                            } else if (row == data[slice].length - 1 && col == data[slice][row].length - 1) {
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                newdata[i][row + 2][col + 1] = data[slice][row][col];
                                newdata[i][row + 1][col + 2] = data[slice][row][col];
                                newdata[i][row + 2][col + 2] = data[slice][row][col];
                            } else {
                                //top side
                                if (row == 0 && col >= 1 && col != data[slice][row].length - 1) {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    newdata[i][row][col + 1] = data[slice][row][col];
                                    //left side
                                } else if (row >= 1 && row != data[slice].length - 1 && col == 0) {
                                    newdata[i][row + 1][col] = data[slice][row][col];
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    //bot side
                                } else if (row == data[slice].length - 1 && col >= 1 && col != data[slice][row].length - 1) {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    newdata[i][row + 2][col + 1] = data[slice][row][col];
                                    //right side
                                } else if (row >= 1 && row != data[slice].length - 1 && col == data[slice][row].length - 1) {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    newdata[i][row + 1][col + 2] = data[slice][row][col];
                                    //center
                                } else {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                }
                            }
                        }
                    } else if (slice == data.length - 1) {
                        for (int i = newdata.length - 2; i < newdata.length; i++) {
                            //top left front
                            if (row == 0 && col == 0) {
                                newdata[i][row][col] = data[slice][row][col];
                                newdata[i][row][col + 1] = data[slice][row][col];
                                newdata[i][row + 1][col] = data[slice][row][col];
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                //top right front
                            } else if (row == 0 && col == data[slice][row].length - 1) {
                                newdata[i][row][col + 1] = data[slice][row][col];
                                newdata[i][row][col + 2] = data[slice][row][col];
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                newdata[i][row + 1][col + 2] = data[slice][row][col];
                                //bot left front
                            } else if (row == data[slice].length - 1 && col == 0) {
                                newdata[i][row + 1][col] = data[slice][row][col];
                                newdata[i][row + 2][col] = data[slice][row][col];
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                newdata[i][row + 2][col + 1] = data[slice][row][col];
                                //bot right front
                            } else if (row == data[slice].length - 1 && col == data[slice][row].length - 1) {
                                newdata[i][row + 1][col + 1] = data[slice][row][col];
                                newdata[i][row + 2][col + 1] = data[slice][row][col];
                                newdata[i][row + 1][col + 2] = data[slice][row][col];
                                newdata[i][row + 2][col + 2] = data[slice][row][col];
                            } else {
                                //top side
                                if (row == 0 && col >= 1 && col != data[slice][row].length - 1) {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    newdata[i][row][col + 1] = data[slice][row][col];
                                    //left side
                                } else if (row >= 1 && row != data[slice].length - 1 && col == 0) {
                                    newdata[i][row + 1][col] = data[slice][row][col];
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    //bot side
                                } else if (row == data[slice].length - 1 && col >= 1 && col != data[slice][row].length - 1) {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    newdata[i][row + 2][col + 1] = data[slice][row][col];
                                    //right side
                                } else if (row >= 1 && row != data[slice].length - 1 && col == data[slice][row].length - 1) {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                    newdata[i][row + 1][col + 2] = data[slice][row][col];
                                    //center
                                } else {
                                    newdata[i][row + 1][col + 1] = data[slice][row][col];
                                }
                            }
                        }
                    } else {
                        //top left front
                        if (row == 0 && col == 0) {
                            newdata[slice + 1][row][col] = data[slice][row][col];
                            newdata[slice + 1][row][col + 1] = data[slice][row][col];
                            newdata[slice + 1][row + 1][col] = data[slice][row][col];
                            newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                            //top right front
                        } else if (row == 0 && col == data[slice][row].length - 1) {
                            newdata[slice + 1][row][col + 1] = data[slice][row][col];
                            newdata[slice + 1][row][col + 2] = data[slice][row][col];
                            newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                            newdata[slice + 1][row + 1][col + 2] = data[slice][row][col];
                            //bot left front
                        } else if (row == data[slice].length - 1 && col == 0) {
                            newdata[slice + 1][row + 1][col] = data[slice][row][col];
                            newdata[slice + 1][row + 2][col] = data[slice][row][col];
                            newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                            newdata[slice + 1][row + 2][col + 1] = data[slice][row][col];
                            //bot right front
                        } else if (row == data[slice].length - 1 && col == data[slice][row].length - 1) {
                            newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                            newdata[slice + 1][row + 2][col + 1] = data[slice][row][col];
                            newdata[slice + 1][row + 1][col + 2] = data[slice][row][col];
                            newdata[slice + 1][row + 2][col + 2] = data[slice][row][col];
                        } else {
                            //top side
                            if (row == 0 && col >= 1 && col != data[slice][row].length - 1) {
                                newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                                newdata[slice + 1][row][col + 1] = data[slice][row][col];
                                //left side
                            } else if (row >= 1 && row != data[slice].length - 1 && col == 0) {
                                newdata[slice + 1][row + 1][col] = data[slice][row][col];
                                newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                                //bot side
                            } else if (row == data[slice].length - 1 && col >= 1 && col != data[slice][row].length - 1) {
                                newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                                newdata[slice + 1][row + 2][col + 1] = data[slice][row][col];
                                //right side
                            } else if (row >= 1 && row != data[slice].length - 1 && col == data[slice][row].length - 1) {
                                newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                                newdata[slice + 1][row + 1][col + 2] = data[slice][row][col];
                                //center
                            } else {
                                newdata[slice + 1][row + 1][col + 1] = data[slice][row][col];
                            }
                        }

                    }
                }
            }
        }

        return newdata;
    }

    public Vector<double[][]> cvt(Vector<double[][][]> filters){
        Vector<double[][]> newfilter=new Vector();
        for(int i=0;i<filters.size();i++){
            double[][][] ary=filter.get(i);
            double[][] newary=new double[ary.length][ary[0].length];
            for(int j=0;j<ary.length;j++){
                for(int k=0;k<ary[i].length;k++){
                    newary[j][k]=ary[j][k][0];
                }
            }
            newfilter.add(newary);
        }
        return newfilter;
    }
    
    public int[][] flip(int[][] crt){
        int[][] newimg=new int[crt[0].length][crt.length];
        for(int i=0;i<newimg.length;i++){
            for(int j=0;j<newimg[0].length;j++){
                newimg[i][j]=crt[j][i];
            }
        }
        return newimg;
    }
    
    public int[][] negate(int[][] img){
        for(int i=0;i<img.length;i++){
            for(int j=0;j<img[0].length;j++){
                img[i][j]=255-img[i][j];
            }
        }
        return img;
    }
    
    public double[][] cvt2dbArr(int[][] img){
        double[][] ary=new double[img.length][img[0].length];
        for(int i=0;i<img.length;i++){
            for(int j=0;j<img[i].length;j++){
                ary[i][j]=(double)img[i][j];
            }
        }
        return ary;
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
    
    public BufferedImage[] getBufferedImageSets(){
        Vector<double[][]> vec=cvt(filter);
        int[][] mag=flip(normalization(vec.get(0),255,0));
        int[][] azi=negate(flip(normalization(vec.get(1),255,0)));
        int[][] pol=negate(flip(normalization(vec.get(2),255,0)));
        int[][] sum=flip(normalization(vec.get(3),255,0));
        int[][] pdt=flip(normalization(vec.get(4),255,0));
        BufferedImage channels[]={int2d2bfi(mag),int2d2bfi(azi),int2d2bfi(pol),int2d2bfi(sum),int2d2bfi(pdt)};
        return channels;
    }

    public Vector<int[][]> getFilter() {
        Vector<double[][]> vec=cvt(filter);
        int[][] mag=flip(normalization(vec.get(0),255,0));
        int[][] azi=negate(flip(normalization(vec.get(1),255,0)));
        int[][] pol=negate(flip(normalization(vec.get(2),255,0)));
        int[][] sum=flip(normalization(vec.get(3),255,0));
        int[][] pdt=flip(normalization(vec.get(4),255,0));
        
        Vector<int[][]> filters=new Vector();
        filters.add(mag);
        filters.add(azi);
        filters.add(pol);
        filters.add(sum);
        filters.add(pdt);
        
        return filters;
    }
}
