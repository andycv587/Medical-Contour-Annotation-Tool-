/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.annotation;

import java.awt.BorderLayout;
import java.awt.ComponentOrientation;
import java.awt.Dimension;
import java.awt.event.AdjustmentEvent;
import java.awt.event.AdjustmentListener;
import java.awt.event.ComponentEvent;
import java.awt.event.ComponentListener;
import javax.swing.JScrollBar;
import java.awt.event.MouseWheelEvent;
import java.awt.event.MouseWheelListener;
import javax.swing.JPanel;
import javax.swing.JScrollPane;

/**
 *
 * @author andy
 */
public class scrollablePanels extends JPanel {

    protected CustomImgPanel[] cips;
    private JScrollPane jsp;
    final JScrollBar sb;
    private int totalnum;
    private WindowDesign wd;

    public scrollablePanels(WindowDesign wd, CustomImgPanel[] cips) {
        this.setSize(new Dimension(850, 800));
        this.wd = wd;
        this.cips = cips;
        this.totalnum = cips.length;
        this.setLayout(new BorderLayout());
        cips[wd.pagenum].setBounds(0, 0, cips[wd.pagenum].getWidth(), cips[wd.pagenum].getHeight());
        sb = new JScrollBar(JScrollBar.VERTICAL, wd.pagenum, 10, 0, cips.length);
        sb.setAlignmentX(JScrollBar.RIGHT_ALIGNMENT);
        sb.setUnitIncrement(1);
        this.add(cips[wd.pagenum], BorderLayout.CENTER);
        this.add(sb, BorderLayout.EAST);

        sb.addAdjustmentListener(new AdjustmentListener() {
            @Override
            public void adjustmentValueChanged(AdjustmentEvent e) {
                remove(cips[wd.pagenum]);
                wd.pagenum = e.getValue();
                setVisible(false);
                add(cips[wd.pagenum], BorderLayout.CENTER);
                setVisible(true);
            }

        });

    }


}
