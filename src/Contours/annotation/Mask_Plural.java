/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package Contours.annotation;

import java.awt.Graphics;
import java.awt.Point;
import java.util.Vector;
import javax.swing.JComponent;

/**
 *
 * @author andy
 */
public class Mask_Plural extends JComponent{
    public Vector<Mask> masks;
    public Vector<Vector<Point>> coodinates;
    public Mask_Plural(Vector<Mask> masks, CustomImgPanel pane){
        this.masks=masks;
        for(int i=0;i<masks.size();i++){
            for(int j=0;j<masks.size();j++){
                
            }
        }
    }
    
    @Override
    public void paintComponent(Graphics g){
        
        
        
    }
    
}
