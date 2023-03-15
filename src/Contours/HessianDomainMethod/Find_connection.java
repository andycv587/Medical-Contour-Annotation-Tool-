/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Contours.HessianDomainMethod;

import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.Vector;
import java.util.Stack;

/**
 * Class State: Finished but not tested
 * @author Andy C
 */
public class Find_connection {

    private int[][] img;
    private int thresholds;

    /*  
     * Constructor
     * Variable Required: Image(BufferedImage), Thresholds set(int[])
     */
    public Find_connection(BufferedImage file, int thresholds) throws IOException {
        this.thresholds = thresholds;
        img = new int[file.getWidth()][file.getHeight()];
        for (int i = 0; i < img.length; i++) {
            for (int j = 0; j < img[i].length; j++) {
                int rgb = file.getRGB(i, j);
                int red = (rgb & 0xff0000) >> 16;
                img[i][j] = red;
            }
        }
        
        this.CvtColor();
        img=this.rotate(img);
    }

    public int[][] rotate(int[][] img){
        int[][] arr=new int[img[0].length][img.length];
        for(int i=0;i<img.length;i++){
            for(int j=0;j<img[i].length;j++){
                arr[j][i]=img[i][j];
            }
        }
        return arr;
    }
    
    
    
    /*
     * Status: done
     * Function: negate color for this picture
     */
    public void CvtColor() {
        for (int i = 0; i < img.length; i++) {
            for (int j = 0; j < img[i].length; j++) {
                img[i][j] = 255 - img[i][j];
            }
        }
    }

    /*
    *  Method part of the find_connection
    *  Return: vector bset
    */
    public Vector<Vector<int[]>> find_connection() {
        Vector<Vector<int[]>> bset =new Vector();
        if (img.length != 0 && img[0].length != 0) {
            int[][] mark = this.ones(img.length,img[0].length);
            for(int i=0;i<mark.length;i++){
                for(int j=0;j<mark[i].length;j++){
                    int pij[]={i,j};
                    if(img[i][j]!=0 || mark[i][j]==0)
                        continue;
                    
                    Vector bsetmask=this.find_sub_connection(mark, pij);
                    Vector<int[]> bsetij=(Vector)bsetmask.get(0);
                    mark=(int[][])bsetmask.get(1);
                    
                    if(bsetij.size()!=0)
                        bset.add(bsetij);
                }
            }

        }

        return bset;
    }

    /*
     * function: find subconnection within 9 blocks
     * Vector has 2 element, 1st is bset, 2d is newmark;
     * Status: Completed, but havent testing yet
     */
    public Vector<Vector> find_sub_connection(int[][] mark, int[] point) {
        Vector vec = new Vector();
        //prequiest(same size for both)
        if (img.length == mark.length && img[0].length == mark[0].length) {
            int imsz[] = {img.length, img[0].length};
            Stack<int[]> q_1 = new Stack();
            q_1.push(point);

            mark[point[0]][point[1]] = 0;
            int n = 0;
            Vector<int[]> bset = new Vector();

            while (q_1.size() != 0) {
                n += 1;
                int[] head = q_1.pop();
                bset.add(head);
                int id_1 = this.positionID(head, imsz);

                int p1[] = {head[0] - 1, head[1] - 1};
                int p2[] = {head[0] - 1, head[1]};
                int p3[] = {head[0] - 1, head[1] + 1};
                int p4[] = {head[0], head[1] + 1};
                int p5[] = {head[0] + 1, head[1] + 1};
                int p6[] = {head[0] + 1, head[1]};
                int p7[] = {head[0] + 1, head[1] - 1};
                int p8[] = {head[0], head[1] - 1};

                if (id_1 == 1) {
                    if (img[p4[0]][p4[1]] == 0 && mark[p4[0]][p4[1]] == 1) {
                        q_1.push(p4);
                        mark[p4[0]][p4[1]] = 0;
                    }
                    if (img[p5[0]][p5[1]] == 0 && mark[p5[0]][p5[1]] == 1) {
                        q_1.push(p5);
                        mark[p5[0]][p5[1]] = 0;
                    }
                    if (img[p6[0]][p6[1]] == 0 && mark[p6[0]][p6[1]] == 1) {
                        q_1.push(p6);
                        mark[p6[0]][p6[1]] = 0;
                    }

                } else if (id_1 == 2) {
                    if (img[p6[0]][p6[1]] == 0 && mark[p6[0]][p6[1]] == 1) {
                        q_1.push(p6);
                        mark[p6[0]][p6[1]] = 0;
                    }
                    if (img[p7[0]][p7[1]] == 0 && mark[p7[0]][p7[1]] == 1) {
                        q_1.push(p7);
                        mark[p7[0]][p7[1]] = 0;
                    }
                    if (img[p8[0]][p8[1]] == 0 && mark[p8[0]][p8[1]] == 1) {
                        q_1.push(p8);
                        mark[p8[0]][p8[1]] = 0;
                    }

                } else if (id_1 == 3) {
                    if (img[p1[0]][p1[1]] == 0 && mark[p1[0]][p1[1]] == 1) {
                        q_1.push(p1);
                        mark[p1[0]][p1[1]] = 0;
                    }
                    if (img[p2[0]][p2[1]] == 0 && mark[p2[0]][p2[1]] == 1) {
                        q_1.push(p2);
                        mark[p2[0]][p2[1]] = 0;
                    }
                    if (img[p8[0]][p8[1]] == 0 && mark[p8[0]][p8[1]] == 1) {
                        q_1.push(p8);
                        mark[p8[0]][p8[1]] = 0;
                    }

                } else if (id_1 == 4) {
                    if (img[p2[0]][p2[1]] == 0 && mark[p2[0]][p2[1]] == 1) {
                        q_1.push(p2);
                        mark[p2[0]][p2[1]] = 0;
                    }
                    if (img[p3[0]][p3[1]] == 0 && mark[p3[0]][p3[1]] == 1) {
                        q_1.push(p3);
                        mark[p3[0]][p3[1]] = 0;
                    }
                    if (img[p4[0]][p4[1]] == 0 && mark[p4[0]][p4[1]] == 1) {
                        q_1.push(p4);
                        mark[p4[0]][p4[1]] = 0;
                    }

                } else if (id_1 == 5) {
                    if (img[p2[0]][p2[1]] == 0 && mark[p2[0]][p2[1]] == 1) {
                        q_1.push(p2);
                        mark[p2[0]][p2[1]] = 0;
                    }
                    if (img[p3[0]][p3[1]] == 0 && mark[p3[0]][p3[1]] == 1) {
                        q_1.push(p3);
                        mark[p3[0]][p3[1]] = 0;
                    }
                    if (img[p4[0]][p4[1]] == 0 && mark[p4[0]][p4[1]] == 1) {
                        q_1.push(p4);
                        mark[p4[0]][p4[1]] = 0;
                    }
                    if (img[p5[0]][p5[1]] == 0 && mark[p5[0]][p5[1]] == 1) {
                        q_1.push(p5);
                        mark[p5[0]][p5[1]] = 0;
                    }
                    if (img[p6[0]][p6[1]] == 0 && mark[p6[0]][p6[1]] == 1) {
                        q_1.push(p6);
                        mark[p6[0]][p6[1]] = 0;
                    }

                } else if (id_1 == 6) {
                    if (img[p4[0]][p4[1]] == 0 && mark[p4[0]][p4[1]] == 1) {
                        q_1.push(p4);
                        mark[p4[0]][p4[1]] = 0;
                    }
                    if (img[p5[0]][p5[1]] == 0 && mark[p5[0]][p5[1]] == 1) {
                        q_1.push(p5);
                        mark[p5[0]][p5[1]] = 0;
                    }
                    if (img[p6[0]][p6[1]] == 0 && mark[p6[0]][p6[1]] == 1) {
                        q_1.push(p6);
                        mark[p6[0]][p6[1]] = 0;
                    }
                    if (img[p7[0]][p7[1]] == 0 && mark[p7[0]][p7[1]] == 1) {
                        q_1.push(p7);
                        mark[p7[0]][p7[1]] = 0;
                    }
                    if (img[p8[0]][p8[1]] == 0 && mark[p8[0]][p8[1]] == 1) {
                        q_1.push(p8);
                        mark[p8[0]][p8[1]] = 0;
                    }

                } else if (id_1 == 7) {
                    if (img[p1[0]][p1[1]] == 0 && mark[p1[0]][p1[1]] == 1) {
                        q_1.push(p1);
                        mark[p1[0]][p1[1]] = 0;
                    }
                    if (img[p2[0]][p2[1]] == 0 && mark[p2[0]][p2[1]] == 1) {
                        q_1.push(p2);
                        mark[p2[0]][p2[1]] = 0;
                    }
                    if (img[p6[0]][p6[1]] == 0 && mark[p6[0]][p6[1]] == 1) {
                        q_1.push(p6);
                        mark[p6[0]][p6[1]] = 0;
                    }
                    if (img[p7[0]][p7[1]] == 0 && mark[p7[0]][p7[1]] == 1) {
                        q_1.push(p7);
                        mark[p7[0]][p7[1]] = 0;
                    }
                    if (img[p8[0]][p8[1]] == 0 && mark[p8[0]][p8[1]] == 1) {
                        q_1.push(p8);
                        mark[p8[0]][p8[1]] = 0;
                    }

                } else if (id_1 == 8) {
                    if (img[p1[0]][p1[1]] == 0 && mark[p1[0]][p1[1]] == 1) {
                        q_1.push(p1);
                        mark[p1[0]][p1[1]] = 0;
                    }
                    if (img[p2[0]][p2[1]] == 0 && mark[p2[0]][p2[1]] == 1) {
                        q_1.push(p2);
                        mark[p2[0]][p2[1]] = 0;
                    }
                    if (img[p3[0]][p3[1]] == 0 && mark[p3[0]][p3[1]] == 1) {
                        q_1.push(p3);
                        mark[p3[0]][p3[1]] = 0;
                    }
                    if (img[p4[0]][p4[1]] == 0 && mark[p4[0]][p4[1]] == 1) {
                        q_1.push(p4);
                        mark[p4[0]][p4[1]] = 0;
                    }
                    if (img[p8[0]][p8[1]] == 0 && mark[p8[0]][p8[1]] == 1) {
                        q_1.push(p8);
                        mark[p8[0]][p8[1]] = 0;
                    }

                } else {
                    if (img[p1[0]][p1[1]] == 0 && mark[p1[0]][p1[1]] == 1) {
                        q_1.push(p1);
                        mark[p1[0]][p1[1]] = 0;
                    }
                    if (img[p2[0]][p2[1]] == 0 && mark[p2[0]][p2[1]] == 1) {
                        q_1.push(p2);
                        mark[p2[0]][p2[1]] = 0;
                    }
                    if (img[p3[0]][p3[1]] == 0 && mark[p3[0]][p3[1]] == 1) {
                        q_1.push(p3);
                        mark[p3[0]][p3[1]] = 0;
                    }
                    if (img[p4[0]][p4[1]] == 0 && mark[p4[0]][p4[1]] == 1) {
                        q_1.push(p4);
                        mark[p4[0]][p4[1]] = 0;
                    }
                    if (img[p5[0]][p5[1]] == 0 && mark[p5[0]][p5[1]] == 1) {
                        q_1.push(p5);
                        mark[p5[0]][p5[1]] = 0;
                    }
                    if (img[p6[0]][p6[1]] == 0 && mark[p6[0]][p6[1]] == 1) {
                        q_1.push(p6);
                        mark[p6[0]][p6[1]] = 0;
                    }
                    if (img[p7[0]][p7[1]] == 0 && mark[p7[0]][p7[1]] == 1) {
                        q_1.push(p7);
                        mark[p7[0]][p7[1]] = 0;
                    }
                    if (img[p8[0]][p8[1]] == 0 && mark[p8[0]][p8[1]] == 1) {
                        q_1.push(p8);
                        mark[p8[0]][p8[1]] = 0;
                    }
                }
            }
            vec.add(bset);
            vec.add(mark);

        }

        return vec;

    }

    public int positionID(int[] point, int[] imsize) {
        int posid = 0;
        if (point[0] == 0 && point[1] == 0) {
            posid = 1;
        } else {
            if (point[0] == 0 && point[1] == imsize[1] - 1) {
                posid = 2;
            } else {
                if (point[0] == 0 && point[1] == imsize[1] - 1) {
                    posid = 2;
                } else {
                    if (point[0] == 0 && point[1] == 0) {
                        posid = 4;
                    } else {
                        if (point[0] != 0 && point[0] != imsize[0] - 1 && point[1] == 0) {
                            posid = 5;
                        } else {
                            if (point[0] == 0 && (point[1] != 0 && point[1] != imsize[1] - 1)) {
                                posid = 6;
                            } else {
                                if ((point[0] != 0 && point[0] != imsize[0] - 1) && point[1] == imsize[1] - 1) {
                                    posid = 7;
                                } else {
                                    if (point[0] == imsize[0] - 1 && (point[1] != 0 && point[1] != imsize[1] - 1)) {
                                        posid = 8;
                                    } else {
                                        posid = 9;
                                    }
                                }
                            }

                        }
                    }
                }
            }
        }
        return posid;
    }

    public Vector filter(int[][] pointset) {
        Vector filtered = new Vector();
        for (int[] row : pointset) {
            if (row.length / 2 > this.thresholds) {
                filtered.add(row);
            }
        }
        return filtered;
    }

    public Vector<Vector<int[]>> contours(Vector<int[][][]> pointset) {
        Vector alll = new Vector();

        Vector<Vector> x = new Vector();
        Vector<Vector> y = new Vector();
        for (int i = 0; i < pointset.size(); i++) {

            Vector num_x = new Vector();
            Vector num_y = new Vector();
            for (int j = 0; j < pointset.get(i).length; j++) {
                for (int k = 0; k < pointset.get(i)[j].length; k++) {
                    num_x.add(pointset.get(i)[j][k][0]);
                    num_y.add(pointset.get(i)[j][k][1]);
                }

            }

            x.add(num_x);
            y.add(num_y);
        }

        for (int i = 0; i < x.size(); i++) {
            if (x.size() != y.size()) {
                break;
            }
            Vector x_i = x.get(i);
            Vector y_j = y.get(i);
            int mxx = this.amax(x_i);

            int mnx = this.amin(x_i);
            int mxy = this.amax(y_j);
            int mny = this.amin(y_j);
            int xls = mxx - mnx + 3;
            int yls = mxy - mny + 3;
            int[][] blank = new int[xls][yls];
            Vector<int[]> curary = new Vector();
            for (int a = 0; a < pointset.size(); a++) {
                for (int j = 0; j < pointset.get(a).length; j++) {
                    //int tmp[] = {pointset.get(a)[j][0] - mnx + 1, pointset.get(a)[j][1] - mny + 1};
                    //curary.add(tmp);
                }
            }
            for (int a = 0; a < curary.size(); a++) {
                //blank[curary.get(a)[0]][curary.get(a)[1]] = 1;
            }

            Vector bondar = new Vector();
            int a = 0;
            while (a < xls) {
                int b = 0;
                while (b < yls) {
                    Vector current = new Vector();
                    if (blank[a][b] == 1) {
                        if (blank[a - 1][b] == 0 || blank[a][b - 1] == 0 || blank[a][b + 1] == 0 || blank[a + 1][b] == 0) {
                            int ary_1[] = {a + mnx - 1, b + mny - 1};
                            current.add(ary_1);
                        }
                        b += 1;
                        if (current.size() != 0) {
                            bondar.add(current);
                        }
                    }

                    a += 1;
                    alll.add(current);
                }
            }
        }
        return alll;
    }

    public int amax(Vector<Vector> vec) {
        int max = 0;
        for (int i = 0; i < vec.size(); i++) {
            for (int j = 0; j < vec.get(i).size(); j++) {
                if (max < (int) vec.get(i).get(j)) {
                    max = (int) vec.get(i).get(j);
                }
            }
        }
        return max;
    }

    public int amin(Vector<Vector> vec) {
        int min = 999999999;
        for (int i = 0; i < vec.size(); i++) {
            for (int j = 0; j < vec.get(i).size(); j++) {
                if (min < (int) vec.get(i).get(j)) {
                    min = (int) vec.get(i).get(j);
                }
            }
        }
        return min;
    }

    public int[][] ones(int[][] zeros) {
        for (int i = 0; i < zeros.length; i++) {
            for (int j = 0; j < zeros[i].length; j++) {
                zeros[i][j] = 1;
            }
        }
        return zeros;
    }
    
    public int[][] ones(int row, int col){
        int[][] res=new int[row][col];
        for(int i=0;i<res.length;i++){
            for(int j=0;j<res[i].length;j++){
                res[i][j]=1;
            }
        }
        return res;
    }
//    
//    public BufferedImage ExportImg(){
//        BufferedImage finalres=new BufferedImage();
//        return finalres;
//    }
    
}
