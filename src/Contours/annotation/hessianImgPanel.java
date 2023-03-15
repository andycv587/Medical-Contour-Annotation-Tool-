package Contours.annotation;

import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.image.BufferedImage;
import java.util.Vector;
import javax.swing.JPanel;

/**
 *
 * @author andy
 */
public class hessianImgPanel extends JPanel {

    private int width = 850;
    private int height = 800;
    private int pagenum;
    private WindowDesign wd;
    Vector<BufferedImage> channel;

    public hessianImgPanel(Vector<BufferedImage> channel, double width, double height, int pagenum, WindowDesign wd) {
        this.wd = wd;
        this.channel = channel;
        this.width = (int) width;
        this.height = (int) height;
        this.pagenum = pagenum;
        setSize((int) width, (int) height);
    }

    public hessianImgPanel() {
    }

    @Override
    public void paintComponent(Graphics g) {
        Graphics2D gs = (Graphics2D) g;
        g.setColor(wd.colorchoice[wd.coloridx]);
        if (wd.nift.length != 0) {
            BufferedImage resized = this.resize(channel.get(pagenum), width, height);
            g.drawImage(resized, 0, 0, width, height, this);
        }
    }

    public BufferedImage resize(BufferedImage img, int col_n, int row_n) {
        Image im = img.getScaledInstance(col_n, row_n, Image.SCALE_SMOOTH);
        BufferedImage bimg = new BufferedImage(col_n, col_n, BufferedImage.TYPE_INT_RGB);
        Graphics2D g2d = bimg.createGraphics();
        g2d.drawImage(im, 0, 0, null);
        return bimg;

    }

}

