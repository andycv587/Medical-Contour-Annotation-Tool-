/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package Contours.HessianDomainMethod;

import java.util.Vector;

/**
 *
 * @author Andy C
 */
class derichefilter_mod {

    //main methods
    public Vector derichefilters_modified(double alpha, int radius, int dim) {
        Vector filter = new Vector();

        if (radius != 0) {
            if (dim > 0 && dim <= 3) {
                double c0 = Math.pow((1 - Math.exp(-alpha)), 2) / (1 + 2 * alpha * Math.exp(-alpha) - Math.exp(-2 * alpha));
                double c1 = -Math.pow((1 - Math.exp(-alpha)), 3) / (2 * alpha * alpha * Math.exp(-alpha) * (1 + Math.exp(-alpha)));
                double c2 = -2 * Math.pow((1 - Math.exp(-alpha)), 4) / (1 + 2 * Math.exp(-alpha) - 2 * Math.exp(-3 * alpha) - Math.exp(-4 * alpha));
                double c3 = (1 - Math.exp(-2 * alpha)) / (2 * alpha * Math.exp(-alpha));
                switch (dim) {
                    case 1:
                        Vector<double[]> filter10 = this.filter_dim_1_0th_order(alpha, c0, radius);
                        Vector<double[]> filter11 = this.filter_dim_1_1th_order(alpha, c1, radius);
                        Vector<double[]> filter12 = this.filter_dim_1_2th_order(alpha, c2, c3, radius);
                        filter.add(filter10.get(0));
                        filter.add(filter11.get(0));
                        filter.add(filter12.get(0));
                        break;
                    case 2:
                        Vector<double[][]> filter20 = this.filter_dim_2_0th_order(alpha, c0, radius);
                        Vector<double[][]> filter21 = this.filter_dim_2_1th_order(alpha, c0, c1, radius);
                        Vector<double[][]> filter22 = this.filter_dim_2_2th_order(alpha, c0, c1, c2, c3, radius);
                        filter.add(filter20.get(0));
                        filter.add(filter21.get(0));
                        filter.add(filter21.get(1));
                        filter.add(filter22.get(0));
                        filter.add(filter22.get(1));
                        filter.add(filter22.get(2));
                        break;
                    case 3:
                        Vector<double[][][]> filter30 = this.filter_dim_3_0th_order(alpha, c0, radius);
                        Vector<double[][][]> filter31 = this.filter_dim_3_1th_order(alpha, c0, c1, radius);
                        Vector<double[][][]> filter32 = this.filter_dim_3_2th_order(alpha, c0, c1, c2, c3, radius);
                        filter.add(filter30.get(0));
                        filter.add(filter31.get(0));
                        filter.add(filter31.get(1));
                        filter.add(filter31.get(2));
                        filter.add(filter32.get(0));
                        filter.add(filter32.get(1));
                        filter.add(filter32.get(2));
                        filter.add(filter32.get(3));
                        filter.add(filter32.get(4));
                        filter.add(filter32.get(5));
                        break;
                    default:
                        System.out.println("fk you error in derichefilters_modified:: wrong num of dim ");
                        break;
                }

            }
        }
        return filter;
    }

    public Vector<Double> f0(int x, double a, double c0) {
        // the return format would [double num]
        Vector<Double> f0 = new Vector();
        //F0=c0*(1+a*abs(x))*math.exp(-1*a*abs(x))
        double num = c0 * (1 + a * Math.abs(x)) * Math.exp(-1 * a * Math.abs(x));
        f0.add(num);
        return f0;
    }

    public Vector<Double> f1(int x, double a, double c1) {
        Vector<Double> f1 = new Vector();
        //F0=-c1*x*a**2*math.exp(-1*a*abs(x));
        double F0 = -c1 * x * a * a * Math.exp(-1 * a * Math.abs(x));
        f1.add(F0);
        return f1;
    }

    public Vector<Double> f2(int x, double a, double c2, double c3) {
        Vector<Double> f2 = new Vector();
        double F0 = c2 * (1 - c3 * a * Math.abs(x)) * Math.exp(-1 * a * Math.abs(x));
        f2.add(F0);
        return f2;
    }

    //when dimension is 1
    public Vector<double[]> filter_dim_1_0th_order(double a, double c0, int radius) {
        Vector<double[]> filter_1 = new Vector();
        if (radius > 1) {
            int rad = Math.abs(radius);
            double[] filter0 = new double[2 * rad + 1];
            for (int x = -rad; x < rad + 1; x++) {
                Vector v = this.f0(x, a, c0);
                double num = (double) v.get(0);
                int idx = x + rad;
                filter0[idx] = num;
            }
            filter_1.add(filter0);
        } else {
            double filter0[] = {-1};
            filter_1.add(filter0);
        }
        return filter_1;
    }

    public Vector<double[]> filter_dim_1_1th_order(double a, double c1, int radius) {
        Vector<double[]> f2 = new Vector();
        if (radius > 1) {
            int rad = Math.abs(radius);
            double[] filter0 = new double[2 * rad + 1];
            for (int x = -rad; x < rad + 1; x++) {
                Vector<Double> v = this.f1(x, a, c1);
                double num = v.get(0);
                int idx = x + rad;
                filter0[idx] = num;
            }
            f2.add(filter0);
        } else {
            double filter1[] = {-1};
            f2.add(filter1);
        }
        return f2;

    }

    public Vector<double[]> filter_dim_1_2th_order(double a, double c2, double c3, int radius) {
        Vector<double[]> f2 = new Vector();
        if (radius > 1) {
            int rad = Math.abs(radius);
            double[] filter0 = new double[2 * rad + 1];
            for (int x = -rad; x < rad + 1; x++) {
                Vector<Double> v = this.f2(x, a, c2, c3);
                double num = v.get(0);
                int idx = x + rad;
                filter0[idx] = num;
            }
            f2.add(filter0);
        } else {
            double filter0[] = {-1};
            f2.add(filter0);
        }
        return f2;
    }

    //when dimension is 2
    public Vector<double[][]> filter_dim_2_0th_order(double a, double c0, int radius) {
        Vector<double[][]> f2 = new Vector();

        if (radius > 1) {
            int rad = Math.abs(radius);
            double[][] filter0 = new double[2 * rad + 1][2 * rad + 1];

            for (int x = -rad; x < rad + 1; x++) {
                double vx = this.f0(x, a, c0).get(0);
                int idx = x + rad;
                for (int y = -rad; y < rad + 1; y++) {
                    double vy = this.f0(y, a, c0).get(0);
                    double v = vy * vx;
                    int idy = y + rad;
                    filter0[idx][idy] = v;
                }
            }
            f2.add(filter0);
        } else {
            double filter0[][] = {{-1}};
            f2.add(filter0);
        }
        return f2;

    }

    public Vector<double[][]> filter_dim_2_1th_order(double a, double c0, double c1, int radius) {
        Vector<double[][]> f2 = new Vector();// total length =2, and 0 is filter x, 1 is filtery

        if (radius > 1) {
            int rad = Math.abs(radius);
            int len_1 = 2 * rad + 1;
            double[][] filterx = new double[len_1][len_1];
            double[][] filtery = new double[len_1][len_1];
            for (int x = -rad; x < rad + 1; x++) {
                double vy0 = this.f0(x, a, c0).get(0);
                double vy1 = this.f1(x, a, c1).get(0);
                int idy = x + rad;
                for (int y = -rad; y < rad + 1; y++) {
                    double vx0 = this.f0(y, a, c0).get(0);
                    double vx1 = this.f1(y, a, c1).get(0);
                    int idx = y + rad;
                    double vx1y0 = vx1 * vy0;
                    double vx0y1 = vx0 * vy1;
                    filterx[idy][idx] = vx1y0;
                    filtery[idy][idx] = vx0y1;
                }
            }
            f2.add(filterx);
            f2.add(filtery);
        } else {
            double filter0[][] = {{-1}};
            f2.add(filter0);
        }
        return f2;

    }

    public Vector<double[][]> filter_dim_2_2th_order(double a, double c0, double c1, double c2, double c3, int radius) {
        Vector<double[][]> f2 = new Vector();
        if (radius > 1) {
            int rad = Math.abs(radius);
            int len_1 = 2 * rad + 1;
            double[][] filterxx = new double[len_1][len_1];
            double[][] filteryy = new double[len_1][len_1];
            double[][] filterxy = new double[len_1][len_1];
            for (int x = -rad; x < rad + 1; x++) {
                double vy0 = this.f0(x, a, c0).get(0);
                double vy1 = this.f1(x, a, c1).get(0);
                double vy2 = this.f2(x, a, c2, c3).get(0);
                int idy = x + rad;
                for (int y = -rad; y < rad + 1; y++) {
                    double vx0 = this.f0(y, a, c0).get(0);
                    double vx1 = this.f1(y, a, c1).get(0);
                    double vx2 = this.f2(y, a, c2, c3).get(0);
                    int idx = y + rad;

                    double vx2y0 = vx2 * vy0;
                    double vx0y2 = vx0 * vy2;
                    double vx1y1 = vx1 * vy1;

                    filterxx[idy][idx] = vx2y0;
                    filteryy[idy][idx] = vx0y2;
                    filterxy[idy][idx] = vx1y1;
                }
            }
            f2.add(filterxx);
            f2.add(filteryy);
            f2.add(filterxy);
        } else {
            double filter0[][] = {{-1}};
            f2.add(filter0);
        }
        return f2;

    }

    //when dimension is 3
    public Vector<double[][][]> filter_dim_3_0th_order(double a, double c0, int radius) {
        Vector<double[][][]> f2 = new Vector();
        if (radius > 0) {
            int rad = Math.abs(radius);
            int len = 2 * rad + 1;
            double[][][] filter0 = new double[len][len][len];
            for (int slice = -rad; slice < rad + 1; slice++) {
                Vector<Double> vz0 = this.f0(slice, a, c0);
                int idz = slice + rad;
                for (int row = -rad; row < rad + 1; row++) {
                    Vector<Double> vy0 = this.f0(row, a, c0);
                    int idy = row + rad;
                    for (int col = -rad; col < rad + 1; col++) {
                        Vector<Double> vx0 = this.f0(col, a, c0);
                        int idx = col + rad;
                        double vx0y0z0 = vz0.get(0) * vy0.get(0) * vx0.get(0);
                        filter0[idz][idy][idx] = vx0y0z0;

                    }
                }
            }
            f2.add(filter0);
        }else{
            double filter0[][][] = {{{-1}}};
            f2.add(filter0);
        }
        return f2;

    }

    public Vector<double[][][]> filter_dim_3_1th_order(double a, double c0, double c1, int radius) {
        Vector<double[][][]> f2 = new Vector();
        if (radius > 0) {
            int rad = Math.abs(radius);
            int len = 2 * rad + 1;
            double[][][] filterx = new double[len][len][len];
            double[][][] filtery = new double[len][len][len];
            double[][][] filterz = new double[len][len][len];
            for (int slice = -rad; slice < rad + 1; slice++) {
                Vector<Double> vz0 = this.f0(slice, a, c0);
                Vector<Double> vz1 = this.f1(slice, a, c1);
                int idz = slice + rad;

                for (int row = -rad; row < rad + 1; row++) {
                    Vector<Double> vy0 = this.f0(row, a, c0);
                    Vector<Double> vy1 = this.f1(row, a, c1);
                    int idy = row + rad;
                    for (int col = -rad; col < rad + 1; col++) {
                        Vector<Double> vx0 = this.f0(col, a, c0);
                        Vector<Double> vx1 = this.f1(col, a, c1);
                        int idx = col + rad;

                        double vx1y0z0 = vx1.get(0) * vy0.get(0) * vz0.get(0);
                        double vx0y1z0 = vx0.get(0) * vy1.get(0) * vz0.get(0);
                        double vx0y0z1 = vx0.get(0) * vy0.get(0) * vz1.get(0);

                        filterx[idz][idy][idx] = vx1y0z0;
                        filtery[idz][idy][idx] = vx0y1z0;
                        filterz[idz][idy][idx] = vx0y0z1;

                    }
                }
            }
            f2.add(filterx);
            f2.add(filtery);
            f2.add(filterz);
        }else{
            double filter0[][][] = {{{-1}}};
            f2.add(filter0);
        }
        return f2;

    }

    public Vector<double[][][]> filter_dim_3_2th_order(double a, double c0, double c1, double c2, double c3, int radius) {
        Vector<double[][][]> f2 = new Vector();
        if (radius > 0) {
            int rad = Math.abs(radius);
            int len = 2 * rad + 1;
            double[][][] filterxx = new double[len][len][len];
            double[][][] filteryy = new double[len][len][len];
            double[][][] filterzz = new double[len][len][len];
            double[][][] filterxy = new double[len][len][len];
            double[][][] filterxz = new double[len][len][len];
            double[][][] filteryz = new double[len][len][len];

            for (int slice = -rad; slice < rad + 1; slice++) {
                Vector<Double> vz0 = this.f0(slice, a, c0);
                Vector<Double> vz1 = this.f1(slice, a, c1);
                Vector<Double> vz2 = this.f2(slice, a, c2, c3);
                int idz = slice + rad;

                for (int row = -rad; row < rad + 1; row++) {
                    Vector<Double> vy0 = this.f0(row, a, c0);
                    Vector<Double> vy1 = this.f1(row, a, c1);
                    Vector<Double> vy2 = this.f2(row, a, c2, c3);
                    int idy = row + rad;
                    for (int col = -rad; col < rad + 1; col++) {
                        Vector<Double> vx0 = this.f0(col, a, c0);
                        Vector<Double> vx1 = this.f1(col, a, c1);
                        Vector<Double> vx2 = this.f2(col, a, c2, c3);
                        int idx = col + rad;

                        double vx2y0z0 = vx2.get(0) * vy0.get(0) * vz0.get(0);
                        double vx0y2z0 = vx0.get(0) * vy2.get(0) * vz0.get(0);
                        double vx0y0z2 = vx0.get(0) * vy0.get(0) * vz2.get(0);

                        double vx1y1z0 = vx1.get(0) * vy1.get(0) * vz0.get(0);
                        double vx1y0z1 = vx1.get(0) * vy0.get(0) * vz1.get(0);
                        double vx0y1z1 = vx0.get(0) * vy1.get(0) * vz1.get(0);

                        filterxx[idz][idy][idx] = vx2y0z0;
                        filteryy[idz][idy][idx] = vx0y2z0;
                        filterzz[idz][idy][idx] = vx0y0z2;

                        filterxy[idz][idy][idx] = vx1y1z0;
                        filterxz[idz][idy][idx] = vx1y0z1;
                        filteryz[idz][idy][idx] = vx0y1z1;

                    }
                }
            }
            f2.add(filterxx);
            f2.add(filteryy);
            f2.add(filterzz);
            f2.add(filterxy);
            f2.add(filterxz);
            f2.add(filteryz);
        }else{
            double filter0[][][] = {{{-1}}};
            f2.add(filter0);
        }
        return f2;

    }

}
