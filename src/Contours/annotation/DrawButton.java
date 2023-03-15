///*
// * Cite from https://www.twblogs.net/a/5c0a5e72bd9eee6fb37b9be6/?lang=zh-cn
// */
//package Contours.annotation;
//
//import java.awt.event.ActionEvent;
//import java.awt.event.ActionListener;
//import java.awt.event.MouseAdapter;
//import java.awt.event.MouseEvent;
//import javax.swing.JPanel;
//import contours.annotation.Page.CustomImgPanel;
//
//public class DrawListen implements ActionListener { 
//
//    private int startX;  
//    private int startY;
//    private int endX;    
//    private int endY;
//    private final CustomImgPanel JPanelWorkOfDraw; 
//
//    public DrawListen(CustomImgPanel JPanelWorkOfDraw) {
//        this.JPanelWorkOfDraw = JPanelWorkOfDraw;
//    }
//    String ButtonType = ""; 
//
//    public void actionPerformed(ActionEvent e) {
//        ButtonType = e.getActionCommand();  
//        JPanelWorkOfDraw.addMouseListener(new MouseAdapter() { 
//            public void mousePressed(MouseEvent e) {  
//                startX = e.getX(); 
//                startY = e.getY();
//            }
//
//            public void mouseReleased(MouseEvent e) {
//                endX = e.getX();  
//                endY = e.getY();
//                if ("Line".equals(ButtonType))    
//                    JPanelWorkOfDraw.getGraphics().drawLine(startX, startY, endX, endY);
//                 else 
//                    System.out.println("Nope, not right command");
//            }
//        });
//    }
//
//}
