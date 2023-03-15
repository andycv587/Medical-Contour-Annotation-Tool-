    /*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.annotation;

import Contours.annotation.WindowDesign;
import java.awt.AWTException;
import java.awt.AlphaComposite;
import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.Point;
import java.awt.Polygon;
import java.awt.Robot;
import java.awt.Scrollbar;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.awt.geom.Line2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.Vector;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.imageio.ImageIO;
import javax.swing.JLabel;
import javax.swing.JPanel;

/**
 *
 * @author andy
 */
public class CustomImgPanel extends JPanel {

    private Utility util = new Utility();
    private int width = 0, height = 0, pagenum, totalpagenum;
    private float transparency;
    public WindowDesign wd;
    public BufferedImage resizednft, resizedmsk, originalnft, originalmsk, backgroundImg;
    public Mask[] masks;
    public Scrollbar sidescroll;
    public double widthfactor = 1, heightfactor = 1;
    public BufferedImage bf1, bf2;
    public Vector<Mask> msks;
    public Vector<Integer> colors;
    public Vector<JLabel[]> contours;
    public Vector<Point> coodinates;
    public Vector<int[]> msksizes;
    public boolean islbl = true;
    public Point point1, point2;
    public Line2D line2d;

    public CustomImgPanel(double width, double height, float transparency, int pagenum, WindowDesign wd) throws IOException {
        super();
        this.setLayout(null);
        this.msksizes = new Vector<int[]>();
        this.wd = wd;
        this.transparency = transparency;
        this.width = (int) width;
        this.height = (int) height;
        setSize((int) width, (int) height);
        this.pagenum = pagenum;
        if (wd.nift.length != 0) {
            this.widthfactor = wd.nift[pagenum].getWidth() / width;
            this.heightfactor = wd.nift[pagenum].getHeight() / height;
            this.originalnft = wd.nift[pagenum];
            this.resizednft = wd.biggerNift[pagenum];
            this.totalpagenum = wd.nift.length;

        } else if (wd.mask.length != 0) {
            this.widthfactor = wd.mask[pagenum].getWidth() / width;
            this.heightfactor = wd.mask[pagenum].getHeight() / height;
            this.originalmsk = wd.mask[pagenum];
            this.resizedmsk = wd.biggeMask[pagenum];
            this.totalpagenum = wd.mask.length;

        }
//        this.bf1 = ImageIO.read(new File("D:\\11111.png"));
//        this.bf2 = ImageIO.read(new File("D:\\asddddd.png"));

        backgroundImg = new BufferedImage(this.width, this.height, BufferedImage.TYPE_INT_ARGB);
        Graphics g = backgroundImg.getGraphics();

        if (wd.nift.length != 0 && wd.mask.length != 0) {
            contours = new Vector<JLabel[]>();
            msks = new Vector<Mask>();
            colors = new Vector<Integer>();
            coodinates = new Vector<Point>();

            for (int i = 0; i < wd.masks[pagenum].length; i++) {
                for (int j = 0; j < wd.masks[pagenum][i].length; j++) {
                    if (!colors.contains(wd.masks[pagenum][i][j]) && wd.masks[pagenum][i][j] != 0) {
                        colors.add(wd.masks[pagenum][i][j]);
                    }
                }
            }
            for (int i = 0; i < colors.size(); i++) {
                Vector<Point> mskk = new Vector<Point>();
                for (int j = 0; j < wd.masks[pagenum].length; j++) {
                    for (int k = 0; k < wd.masks[pagenum][i].length; k++) {
                        if (wd.masks[pagenum][j][k] == colors.get(i)) {
                            mskk.add(new Point(j, k));
                        }
                    }
                }
                Mask mk = new Mask(mskk, this, wd.coloridx);
                msks.add(mk);
//                System.out.println("this is "+i);
                Color argb = new Color(0.7f, 0.33f, 0.54f, 1.0f);
                switch (colors.get(i)) {
                    case 51:
                        argb = new Color(1.0f, 0f, 0f, 1.0f);
                        break;
                    case 85:
                        argb = new Color(0f, 1.0f, 0f, 1.0f);
                        break;
                    case 127:
                        argb = new Color(0f, 0f, 1.0f, 1.0f);
                        break;
                    case 170:
                        argb = new Color(1.0f, 1.0f, 0f, 1.0f);
                        break;
                    case 204:
                        argb = new Color(0f, 1.0f, 1.0f, 1.0f);
                        break;
                    case 255:
                        argb = new Color(1.0f, 0f, 1.0f, 1.0f);
                        break;
                }

                JLabel[] lbl1 = mk.makeMask(argb);
                contours.add(lbl1);
                coodinates.add(mk.getLeftTopCorner());
            }

            for (int i = 0; i < contours.size(); i++) {
                JLabel[] lbls = contours.get(i);
                JLabel lbl = lbls[0];
                Mask mk = msks.get(i);
                Vector<Point> v = mk.getResizedmasks();

                int x = coodinates.get(i).x;
                int y = coodinates.get(i).y;
                int sx = msksizes.get(i)[0];
                int sy = msksizes.get(i)[1];

                lbl.setBounds(x, y, sx, sy);
                this.add(lbl);
                this.repaint();
            }
        }
        wd.contours=this.contours;
    }

    @Override
    public void paintComponent(Graphics g) {
        super.paintComponent(g);
        if (wd.nift.length == 0) {
            g.drawImage(wd.mask[pagenum], 0, 0, this.width, this.height, this);
            if(wd.fromwtsd!=null){
                
            }
//            saveImage();
        } else if (wd.mask.length == 0) {
            g.drawImage(wd.nift[pagenum], 0, 0, this.width, this.height, this);
        } else {
            g.drawImage(wd.nift[pagenum], 0, 0, this.width, this.height, this);
        }

//        if (wd.clickpaint == true) {
//            Graphics2D g2d = (Graphics2D) g;
//            if (point1 != null && point2 != null) {
//
//                g2d.setPaint(Color.RED);
//                g2d.setStroke(new BasicStroke(1.5f));
//                g2d.draw(line2d);
//
//            }
//
//        }

    }

    /*
     * nft:a=0
     * msk:a=1
     * layover: a= all others
     */
    public BufferedImage getresized(int a) throws IOException {
        if (resizednft == null) {
            return resizedmsk;
        } else if (resizedmsk == null) {
            return resizednft;
        } else {
            if (a == 0) {
                return resizednft;
            } else if (a == 1) {
                return resizedmsk;
            } else {
                return layeroverlay(resizednft, resizedmsk, transparency);
            }
        }
    }

    public double[] getfactors() {
        double arr[] = {widthfactor, heightfactor};
        return arr;
    }

    public BufferedImage layeroverlay(BufferedImage img, BufferedImage mask, float alpha) throws IOException {
        int imgcol = img.getWidth();
        int imgrow = img.getHeight();
        BufferedImage msk = util.resize(mask, imgcol, imgrow);
        BufferedImage nimg = img;
        Graphics2D g2d = nimg.createGraphics();
        g2d.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_ATOP, alpha));
        g2d.drawImage(msk, 0, 0, imgcol, imgrow, null);
        return nimg;
    }

    public BufferedImage getOriginalscale() throws IOException {
        if (originalnft == null) {
            return originalmsk;
        } else if (originalmsk == null) {
            return originalnft;
        } else {
            return layeroverlay(originalnft, originalmsk, transparency);
        }
    }

    public void saveImage(String path) {
        Dimension size = this.getSize();
        BufferedImage image = new BufferedImage(size.width, size.height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g2 = image.createGraphics();
        this.paint(g2);
        try {
            ImageIO.write(image, "png", new File(path));
            System.out.println("panel saved as image");

        } catch (Exception e) {
            System.out.println("panel not saved" + e.getMessage());
        }
    }

}
