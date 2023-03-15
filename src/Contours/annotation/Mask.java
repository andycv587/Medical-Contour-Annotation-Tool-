/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.annotation;

import java.io.File;
import java.io.IOException;
import java.util.Vector;
import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.swing.ImageIcon;
import javax.swing.JLabel;

/**
 *
 * @author andy
 */
public class Mask {

    //resized masks, original point is msk;
    private Vector<Point> masks, msk = new Vector<Point>(), OriginalsizeContour = new Vector<Point>(), MasksizeContour = new Vector<Point>();
    private BufferedImage bf, resized, ori;
    private CustomImgPanel pane;
    private double widthfactor, heightfactor;
    private int coloridx, LeftX, LeftY, width = 0, height = 0;
    public int nw, nh;
    private Color cla;
    private Utility ut;
    
    public Mask(Vector<Point> masks, CustomImgPanel pane, int coloridx) throws IOException {
        this.masks = masks;
        this.bf = pane.originalnft;
        this.widthfactor = pane.getfactors()[0];
        this.heightfactor = pane.getfactors()[1];
        this.pane = pane;
        this.resized = pane.getresized(1);
        this.ori = pane.originalmsk;
        this.coloridx = coloridx;
        this.cla = pane.wd.colorchoice[coloridx];
        this.ut = new Utility();

        for (Point p : masks) {
            int x = (int) (p.x);
            int y = (int) (p.y);
            Point p1 = new Point(x, y);
            this.msk.add(p1);
        }

        for (int i = 0; i < msk.size(); i++) {
            Point p = msk.get(i);
            for (int j = i + 1; j < msk.size(); j++) {
                if (msk.get(j).equals(p)) {
                    this.msk.remove(j);
                }
            }
        }

        this.setContours();

//        ActionListener a1 = new ActionListener() {
//            Point lastPoint;
//
//            @Override
//            public void actionPerformed(ActionEvent e) {
//                Point p = MouseInfo.getPointerInfo().getLocation();
//                if (masks.contains(p)) {
//
//                }
//                lastPoint = p;
//            }
//
//        };
    }
    
    
    public String getPoints() {
        return "This mask contains: " + masks.size() + " points";
    }

    public Vector<Point> getResizedmasks() {
        return masks;
    }

    public Vector<Point> getOriginalmasks() {
        return msk;
    }

    public BufferedImage getOriginalSizeMask() {
        for (Point p : msk) {
            switch (coloridx) {
                case 0://grayscale
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y) << 16 | ori.getRGB(p.x, p.y) << 8 | ori.getRGB(p.x, p.y));
                    break;
                case 1://red
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y) << 16);
                    break;
                case 2://cyan
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y) << 8 | ori.getRGB(p.x, p.y));
                    break;
                case 3://yellow
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y) << 16 | ori.getRGB(p.x, p.y) << 8);
                    break;
                case 4://green
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y) << 16 | ori.getRGB(p.x, p.y));
                    break;
                case 5://blue
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y));
                    break;
                case 6://pink
                    ori.setRGB(p.x, p.y, ori.getRGB(p.x, p.y) << 16 | ori.getRGB(p.x, p.y));
                    break;
            }
        }
        return ori;
    }

    public BufferedImage getResizedMask() {
        for (Point p : masks) {
            switch (coloridx) {
                case 0://grayscale
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y) << 16 | resized.getRGB(p.x, p.y) << 8 | resized.getRGB(p.x, p.y));
                    break;
                case 1://red
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y) << 16);
                    break;
                case 2://cyan
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y) << 8 | resized.getRGB(p.x, p.y));
                    break;
                case 3://yellow
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y) << 16 | resized.getRGB(p.x, p.y) << 8);
                    break;
                case 4://green
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y) << 16 | resized.getRGB(p.x, p.y));
                    break;
                case 5://blue
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y));
                    break;
                case 6://pink
                    resized.setRGB(p.x, p.y, resized.getRGB(p.x, p.y) << 16 | resized.getRGB(p.x, p.y));
                    break;
            }
        }
        System.out.println("resized");
        return ori;
    }

    public void contrastTwo(Mask AnotherMask) {
        Vector<Point> points = AnotherMask.getResizedmasks();

        for (int i = 0; i < points.size(); i++) {
            for (int j = 0; j < masks.size(); j++) {
                if (points.get(i).equals(masks.get(j))) {
                    masks.remove(j);
                    break;
                }
            }
        }
    }

    public void saveOriginalmask(String path) throws IOException {
        BufferedImage bfi = new BufferedImage(ori.getWidth(), ori.getHeight(), bf.TYPE_INT_RGB);
        for (int i = 0; i < bfi.getWidth(); i++) {
            for (int j = 0; j < bfi.getHeight(); j++) {
                bfi.setRGB(i, j, 0);
            }
        }
        for (Point p : msk) {
            bfi.setRGB(p.x, p.y, 255);
        }
        File fi = new File(path);
        ImageIO.write(bfi, "png", fi);
    }

    public void saveResizedmask(String path) throws IOException {
        BufferedImage bfi = new BufferedImage(resized.getWidth(), resized.getHeight(), bf.TYPE_INT_RGB);
        for (int i = 0; i < bfi.getWidth(); i++) {
            for (int j = 0; j < bfi.getHeight(); j++) {
                bfi.setRGB(i, j, 0);
            }
        }
        for (Point p : masks) {
            bfi.setRGB(p.x, p.y, 255);
        }
        File fi = new File(path);
        ImageIO.write(bfi, "png", fi);
    }

    public int Size() {
        return masks.size();
    }

    public void dilatecontours(double factor) {

    }

    public void setContours() {
        int[][] img = ut.convert2intFormat2D(bf);
        LeftX = img.length;
        LeftY = img[0].length;
        int[][] newmask = new int[img.length][img[0].length];
        for (Point p : masks) {
            newmask[p.x][p.y] = 255;
        }

//        for (int i = 0; i < newimg.length; i++) {
//            for (int j = 0; j < newimg[i].length; j++) {
//                if (newimg[i][j] == 0) {
//                    System.out.print(" 000");
//                } else {
//                    System.out.print(" " + newimg[i][j]);
//                }
//            }
//            System.out.println();
//        }
        for (int i = 0; i < masks.size(); i++) {
            int x = masks.get(i).x;
            int y = masks.get(i).y;
            if (x < LeftX) {
                LeftX = x;
            }
            if (y < LeftY) {
                LeftY = y;
            }

            if (x > width) {
                width = x;
            }
            if (y > height) {
                height = y;
            }

            if (x == 0 || y == 0 || x == newmask.length || y == newmask[0].length) {
                OriginalsizeContour.add(new Point(x, y));
            } else {
                if (newmask[x][y] == 255) {
                    if (newmask[x + 1][y - 1] == 0 || newmask[x + 1][y] == 0 || newmask[x + 1][y + 1] == 0 || newmask[x][y - 1] == 0 || newmask[x][y + 1] == 0 || newmask[x - 1][y - 1] == 0 || newmask[x - 1][y] == 0 || newmask[x - 1][y + 1] == 0) {
                        OriginalsizeContour.add(new Point(x, y));
                    }
                }
            }
        }
        width = width - LeftX + 1;
        height = height - LeftY + 1;
        Vector<Point> newcon = new Vector<Point>();
        int a = OriginalsizeContour.size() / 2;
        if (OriginalsizeContour.size() % 2 == 1) {
            a += 1;
        }
        for (int i = 0; i < a; i++) {
            newcon.add(OriginalsizeContour.get(2 * i));
            OriginalsizeContour.set(2 * i, new Point(-1, -1));
        }

        for (int i = 0; i < OriginalsizeContour.size(); i++) {
            if (!OriginalsizeContour.get(i).equals(new Point(-1, -1))) {
                newcon.add(OriginalsizeContour.get(i));
            }
        }

        OriginalsizeContour = newcon;

    }

    public Vector<Point> getContours() {
        return OriginalsizeContour;
    }

    public Point getLeftTopCorner() {
        return new Point((int) ((LeftX + 1) / pane.widthfactor), (int) ((LeftY + 1) / pane.heightfactor));
    }

    public JLabel[] makeMask(Color argbcolor) throws IOException {
        JLabel[] lbs = new JLabel[2];
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        BufferedImage image_1 = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        for (Point p : OriginalsizeContour) {
            MasksizeContour.add(new Point(p.x - LeftX, p.y - LeftY));
        }
        for (int i = 0; i < width; i++) {
            for (int j = 0; j < height; j++) {
                Point p = new Point(i, j);
                if (!MasksizeContour.contains(p)) {
                    image.setRGB(i, j, new Color(0f,0f,0f,0f).getRGB());
                    image_1.setRGB(i, j, new Color(0f,0f,0f,0f).getRGB());
                } else {
                    image.setRGB(i, j, argbcolor.getRGB());
                    image_1.setRGB(i, j, new Color(1.0f, (float) (101.0 / 255.0), (float) (80.0 / 255.0), 1f).getRGB());
                }
            }
        }

        int nw = (int) (width / widthfactor);
        int nh = (int) (height / heightfactor);
        int[] nsize = {nw, nh};
        pane.msksizes.add(nsize);
//        BufferedImage resized_1 = ut.resize(image, nw, nh);
        BufferedImage b = new BufferedImage(nw, nh, BufferedImage.TYPE_INT_ARGB);
        Graphics2D gs = b.createGraphics();
        ImageIcon ii = new ImageIcon(b);
        gs.drawImage(image, 0, 0, nw, nh, null);
//        ImageIO.write(b, "png", new File("D:\\qwer.png"));
        JLabel jl = new JLabel(ii);
        jl.setSize(nw, nh);
        jl.setOpaque(false);

        BufferedImage c = new BufferedImage(nw, nh, BufferedImage.TYPE_INT_ARGB);
        Graphics2D gs1 = c.createGraphics();
        ImageIcon ii1 = new ImageIcon(c);
        gs1.drawImage(image_1, 0, 0, nw, nh, null);

        
        JLabel jl1 = new JLabel(ii1);
        jl1.setSize(nw, nh);
        jl1.setOpaque(false);

        lbs[0] = jl;
        lbs[1] = jl1;

        return lbs;
    }

}
