package Contours.annotation;

import java.awt.*;
import javax.swing.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.Vector;
import java.util.logging.*;
import javax.swing.event.ChangeListener;
import javax.swing.event.ChangeEvent;
import javax.swing.border.LineBorder;
import Contours.HessianDomainMethod.*;
import Contours.WatershedMethod.Watershed;
import javax.imageio.ImageIO;
import Contours.niftijio.NiftiVolume;
import org.opencv.core.Mat;
import Contours.Components.Slider.*;

/*
 * @author(s) Andy C, Aidan C, James T
 * functions needed()
 *      1. Botmenutool(change to tab pane)
 *          a) Our Method(status: developed, before 4-8-2022)
 *          b) level set Method(status: underdeveloped, before 4-15-2022)
 *          c) Watershed Method(status: underdeveloped, before 4-15-2022)
 *          d) Manually entry annotation(status: developing, before 4-15-2022)
 *      2. Save contours(have not started yet, before 4-15-2022)
 *      3. label based of rgb image(have not start yet, before 4-15-2022)
 *      4. selection of contours by user(have not start yet, before 4-15-2022)
 *      5. Bugs on radiobuttons(all of em)(add spinner cannot close)(line 110-319)
 */
public class WindowDesign extends JFrame implements MouseWheelListener {

    public WindowDesign() throws IOException {
        initComponents();
    }

    /*all components of the app
        status: underdeveloped(2:49 am - 4/3/2022)
     */
    @SuppressWarnings("unchecked")
    private void initComponents() throws IOException {

        this.setTitle("Contour Annotation Tool");
        this.setSize(1000, 800);

        this.initializers();
        this.BasicLayout();
        this.FunctionLayout();
        this.hessianWindow();
        jPanelFreeAnnotation.add(jButtonStartFreeAnotation);
        jButtonStartFreeAnotation.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                if (jimgpanels != null) {
                    jPanelFreeAnnotation.add(jButtonEndAnnote);
                    System.out.println("activited");
                    jimgpanels[pagenum].getGraphics().setColor(colorchoice[coloridx]);
                    jimgpanels[pagenum].addMouseListener(new MouseAdapter() {
                        public void mousePressed(MouseEvent e) {
                            Vector<Point> pointcrt = util.FindLine(startX, startY, endX, endY);
                            if (isfirst == true) {
                                startX = e.getX();
                                startY = e.getY();
                                firstX = startX;
                                firstY = startY;
                            } else if (firstX == endX && firstY == endY && started == true) {
                                endX = e.getX();
                                endY = e.getY();
                                System.out.println("done 1");
                                jimgpanels[pagenum].getGraphics().setColor(colorchoice[coloridx]);
                                Vector<Point> points = util.FindLine(startX, startY, endX, endY);
                                pointset = util.extendVec(pointset, points);
                                contourset.add(pointset);
                                jimgpanels[pagenum].getGraphics().drawLine(startX, startY, endX, endY);
                                isfirst = true;
                            } else if (util.issame(pointset, pointcrt) == true && started == true) {
                                endX = e.getX();
                                endY = e.getY();
                                System.out.println("done 2");
                                Vector<Point> points = util.FindLine(startX, startY, endX, endY);
                                pointset = util.extendVec(pointset, points);
                                contourset.add(pointset);
                                jimgpanels[pagenum].getGraphics().setColor(colorchoice[coloridx]);
                                jimgpanels[pagenum].getGraphics().drawLine(startX, startY, endX, endY);
                                isfirst = true;
                            } else {
                                endX = e.getX();
                                endY = e.getY();
                                Vector<Point> points = util.FindLine(startX, startY, endX, endY);
                                points.remove(new Point(endX, endY));
                                pointset = util.extendVec(pointset, points);
                                jimgpanels[pagenum].getGraphics().setColor(colorchoice[coloridx]);
                                jimgpanels[pagenum].getGraphics().drawLine(startX, startY, endX, endY);
                                startX = endX;
                                startY = endY;
                                started = true;
                            }
                            System.out.println("Start is " + startX + "," + startY);
                        }

                        public void mouseReleased(MouseEvent e) {
                            if (isfirst == true) {
                                endX = e.getX();
                                endY = e.getY();
                                Vector<Point> points = util.FindLine(startX, startY, endX, endY);
                                pointset = util.extendVec(pointset, points);
                                jimgpanels[pagenum].getGraphics().setColor(colorchoice[coloridx]);
                                jimgpanels[pagenum].getGraphics().drawLine(startX, startY, endX, endY);
                                startX = endX;
                                startY = endY;
                                isfirst = false;
                            }
                        }
                    });
                    jimgpanels[pagenum].addKeyListener(new KeyListener() {
                        @Override
                        public void keyTyped(KeyEvent ke) {
                            System.out.println("typed" + ke.getKeyCode());
                        }

                        @Override
                        public void keyPressed(KeyEvent ke) {
                            System.out.println("pressed:" + ke.getKeyCode());
                        }

                        @Override
                        public void keyReleased(KeyEvent ke) {
                            System.out.println("released" + ke.getKeyCode());
                        }

                    });

                }
            }

        });

        jButtonEndAnnote.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                System.out.println("done endd");
                jButtonEndAnnote.setVisible(true);
                jimgpanels[pagenum].getGraphics().setColor(colorchoice[coloridx]);
                Vector<Point> points = util.FindLine(firstX, firstY, endX, endY);
                pointset = util.extendVec(pointset, points);
                contourset.add(pointset);
                jimgpanels[pagenum].getGraphics().drawLine(firstX, firstY, endX, endY);
                try {
                    turncolor(coloridx);
                } catch (IOException ex) {
                    Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                }
                jSplitPane1.remove(jimgpanels[pagenum]);
                jimgpanels[pagenum].setVisible(false);
                jSplitPane1.remove(jimgpanels[pagenum]);
                try {
                    jimgpanels[pagenum] = new CustomImgPanel(850, 800, transparency, pagenum, wd);
                } catch (IOException ex) {
                    Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                }
                niftis = util.cvtdb3d2int3d(util.convert2intArry(nift));
                jSplitPane1.setRightComponent(jimgpanels[pagenum]);
                isfirst = true;
            }

        });

        jButtonsaveContours.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {

                for (BufferedImage img : biggeMask) {
                    finalcontours.add(img);
                }

//                savedmaskfile
//                savedmaskfile
                JFileChooser chooser = new JFileChooser();
                chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                int returnVal = chooser.showOpenDialog(jButtondicoms);
                if (returnVal == JFileChooser.APPROVE_OPTION) {
                    String savepath = chooser.getSelectedFile().getAbsolutePath();

                }

            }

        });

        jButtonClearLabel.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {

            }

        });

        jButttonDeleteSelectedLabel.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {

            }

        });

        this.segmentationpart();

        this.WatershedWindow();

        this.LevelSetWindow();

        this.setResizable(false);

        this.pack();
    }

    /*
    * initializer
    * Status: finished(add when need)
     */
    private void initializers() {
        sidescroll = new Scrollbar();
        jSplitPane1 = new JSplitPane();
        jSplitPane3 = new JSplitPane();
        jSplitPane4 = new JSplitPane();
        jSplitPane5 = new JSplitPane();
        jSplitPane6 = new JSplitPane();
        jSplitPaneHessian1 = new JSplitPane();
        jSplitPaneHessian2 = new JSplitPane();
        jSplitPaneHessian3 = new JSplitPane();

        jPanelLevelset = new JPanel();
        jPanelRunOption = new JPanel();
        jPanelTopMenuTool = new JPanel();
        jPanelBotMenuTool = new JPanel();
        jPanellisttop = new JPanel();
        jPanelHessianMethod = new JPanel();
        jPanelFreeAnnotation = new JPanel();
        jPanelmiddleworshop = new JPanel();
        jPanelHessianRadioSpin = new JPanel();
        jPanelImgDisplay = new JPanel();
        jPanelHessianImgAction = new JPanel();
        jPanelWatershed = new JPanel();
        jPanelWarning = new JPanel();

        jSliderMaxWindowsLvl = new RangeSlider(0, 100);
        jSliderTransparency = new JSlider(0, 100);
        jSliderMinWindowsLvl = new RangeSlider(0, 100);
        jSpinnerMaxWindowsLvl = new JLabel();
        jSpinnerMinWindowsLvl = new JLabel();
        jSpinnerTransparency = new JLabel();
        jsmag = new JSpinner();
        jsazi = new JSpinner();
        jspol = new JSpinner();
        jssum = new JSpinner();
        jspdt = new JSpinner();

        lblCurrentPics = new JLabel("No Channel", SwingConstants.CENTER);
        initial = new JLabel();
        maxlvl = new JLabel();
        minlvl = new JLabel();
        lblsegtime = new JLabel("Iterate Time(2^n)");
        lblthresholdset = new JLabel("Threshold Set");
        lblretreatratio = new JLabel("Retreat Ratio");
        lblfilter = new JLabel("Filter value");
        transparencylvl = new JLabel();
        lblwinradius = new JLabel();
        lblmappingpower = new JLabel();
        lblalpha = new JLabel();
        lblnullCT = new JLabel();
        lblwtsdhighthreshold = new JLabel("High threshold");
        lblwtsdlowthreshold = new JLabel("low threshold");
        lblklengthx = new JLabel("Kernel length x");
        lblklengthy = new JLabel("Kernel length y");
        lbliternum = new JLabel("Iterate Number");
        lbllambdal = new JLabel("Lambdal");
        lblnu = new JLabel("Nu");
        lblmu = new JLabel("Mu");
        lbltimestep = new JLabel("Time Step");
        lblepsilon = new JLabel("Epsilon");

        listFileChooser = new List();
        listMaskChooser = new List();

        jButtonApply = new JButton();
        jButtonEndAnnote = new JButton();
        jButtonReadyHessianChannel = new JButton();
        jButtonClearLabel = new JButton();
        jButttonDeleteSelectedLabel = new JButton();
        jButtonHessianShow = new JButton();
        jButtonMasks = new JButton();
        jButtondicoms = new JButton();
        jButtonHessianRun = new JButton();
        jButtonsaveContours = new JButton();
        jButtonStartFreeAnotation = new JButton();
        jButtonHessianRight = new JButton();
        jButtonHessianLeft = new JButton();
        jButtonDoWatershed = new JButton();
        jButtonSelect = new JButton();
        jButtonDoLevelset = new JButton();
        

        maskPath = new JTextField();
        dicomPath = new JTextField();
        txtwinradius = new JTextField();
        txtmappingpower = new JTextField();
        txtalpha = new JTextField();
        txtthresholdset = new JTextField();
        txtretreatratio = new JTextField();
        txtfilter = new JTextField();
        txtnullCT = new JTextField();
        txtsegtime = new JTextField();
        txtwtsdhighthreshold = new JTextField();
        txtwtsdlowthreshold = new JTextField();
        txtklengthx = new JTextField();
        txtklengthy = new JTextField();
        txtiternum = new JTextField();
        txtlambdal = new JTextField();
        txtnu = new JTextField();
        txtmu = new JTextField();
        txttimestep = new JTextField();
        txtepsilon = new JTextField();

        distractTab = new JTabbedPane();
        botMenu = new JTabbedPane();
        rendrar = new ComboBoxRenderar();
        JRBMag = new JCheckBox();
        JRBAzi = new JCheckBox();
        JRBPol = new JCheckBox();
        JRBPdt = new JCheckBox();
        JRBSum = new JCheckBox();
        JRBISAll = new JCheckBox();
        JRBISALLlevelset = new JCheckBox();

        jFrameHessian = new JFrame();
        jFrameWarning = new JFrame();
        hip = new hessianImgPanel();
        jPanelHessianRadioButtons = new JScrollPane(jPanelHessianRadioSpin);

    }

    /*
    * Basic Layout and functions of Hessianwindows
    * Status: under-developed
     */
    private void hessianWindow() {
        int width = 800, height = 600;
        jFrameHessian.getContentPane().add(jSplitPaneHessian1);
        jFrameHessian.setResizable(false);
        jSplitPaneHessian1.setOrientation(JSplitPane.VERTICAL_SPLIT);
        jSplitPaneHessian1.setDividerLocation(100);
        jSplitPaneHessian1.setBorder(new LineBorder(Color.black, 1));
        jSplitPaneHessian1.setEnabled(false);
        jSplitPaneHessian1.setTopComponent(jSplitPaneHessian2);
        jSplitPaneHessian1.setBottomComponent(jPanelImgDisplay);
        jSplitPaneHessian2.setDividerLocation(600);
        jSplitPaneHessian2.setRightComponent(jPanelHessianImgAction);
        jSplitPaneHessian2.setLeftComponent(jSplitPaneHessian3);
        jSplitPaneHessian2.setBorder(new LineBorder(Color.black, 1));
        jSplitPaneHessian2.setEnabled(false);
        jSplitPaneHessian3.setDividerLocation(150);
        jSplitPaneHessian3.setLeftComponent(jPanelHessianRadioButtons);
        jSplitPaneHessian3.setRightComponent(jPanelRunOption);
        jSplitPaneHessian3.setBorder(new LineBorder(Color.black, 1));
        jSplitPaneHessian3.setEnabled(false);

        ImageIcon Right = new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/DisplayRight.png"));
        jButtonHessianRight.setIcon(Right);
        jButtonHessianRight.setToolTipText("next Channel");

        ImageIcon Left = new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/DisplayLeft.png"));
        jButtonHessianLeft.setIcon(Left);
        jButtonHessianLeft.setToolTipText("previous Channel");

        jButtonHessianShow.setText("Run Segment");
        jButtonHessianShow.setPreferredSize(new Dimension(70, 30));
        jButtonHessianRun.setText("Show Sample");
        jButtonHessianRun.setPreferredSize(new Dimension(70, 30));
        lblwinradius.setText("Win-Radius");
        lblmappingpower.setText("MappingPow");
        lblalpha.setText("AlphaValue");
        lblnullCT.setText("NullCTValue");
        txtwinradius.setPreferredSize(new Dimension(70, 30));
        txtmappingpower.setPreferredSize(new Dimension(70, 30));
        txtalpha.setPreferredSize(new Dimension(70, 30));
        txtnullCT.setPreferredSize(new Dimension(70, 30));

        GroupLayout jPanelPanelRunLayout = new GroupLayout(jPanelRunOption);

        jPanelRunOption.setLayout(jPanelPanelRunLayout);
        jPanelPanelRunLayout.setHorizontalGroup(
                jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelPanelRunLayout.createSequentialGroup()
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(lblwinradius)
                                        .addComponent(lblmappingpower))
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(txtwinradius)
                                        .addComponent(txtmappingpower))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(lblalpha)
                                        .addComponent(lblnullCT))
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(txtalpha)
                                        .addComponent(txtnullCT))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(jButtonHessianRun)
                                        .addComponent(jButtonHessianShow))
                        )
        );
        jPanelPanelRunLayout.setVerticalGroup(
                jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelPanelRunLayout.createSequentialGroup()
                                .addContainerGap()
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblwinradius, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtwinradius)
                                        .addComponent(lblalpha, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtalpha)
                                        .addComponent(jButtonHessianRun, GroupLayout.Alignment.CENTER))
                                .addGroup(jPanelPanelRunLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblmappingpower, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtmappingpower)
                                        .addComponent(lblnullCT, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtnullCT)
                                        .addComponent(jButtonHessianShow, GroupLayout.Alignment.CENTER)))
        );

        jButtonHessianShow.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent ae) {

            }

        });

        lblCurrentPics.setSize(new Dimension(100, 100));

        jPanelHessianImgAction.setLayout(new BorderLayout());
        jPanelHessianImgAction.add(jButtonHessianLeft, BorderLayout.WEST);
        jPanelHessianImgAction.add(lblCurrentPics, BorderLayout.CENTER);
        jPanelHessianImgAction.add(jButtonHessianRight, BorderLayout.EAST);
        jButtonHessianRight.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent ae) {
                if (isplayingchannel == true) {
                    if (crtchannel < 4) {
                        crtchannel += 1;
                    }
                    lblCurrentPics.setText(channel[crtchannel]);
                    hessianImgPanel hip = channelspanel.get(crtchannel);
                    jSplitPaneHessian1.setBottomComponent(hip);
                    hip.setVisible(true);
                    jSplitPaneHessian1.setVisible(true);
                    isplayingchannel = true;

                }
            }

        });
        jButtonHessianLeft.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent ae) {
                if (isplayingchannel == true) {
                    if (crtchannel >= 0) {
                        crtchannel -= 1;
                    }
                    lblCurrentPics.setText(channel[crtchannel]);
                    hessianImgPanel hip = channelspanel.get(crtchannel);
                    jSplitPaneHessian1.setBottomComponent(hip);
                    hip.setVisible(true);
                    jSplitPaneHessian1.setVisible(true);
                    isplayingchannel = true;

                }
            }

        });

        GroupLayout jPanelratioLayout = new GroupLayout(jPanelHessianRadioSpin);
        jPanelHessianRadioSpin.setLayout(jPanelratioLayout);
        jPanelratioLayout.setHorizontalGroup(
                jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelratioLayout.createSequentialGroup()
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(JRBMag)
                                        .addComponent(JRBAzi)
                                        .addComponent(JRBPol)
                                        .addComponent(JRBPdt)
                                        .addComponent(JRBSum))
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(jsmag)
                                        .addComponent(jsazi)
                                        .addComponent(jspol)
                                        .addComponent(jssum)
                                        .addComponent(jspdt))
                        )
        );
        jPanelratioLayout.setVerticalGroup(
                jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelratioLayout.createSequentialGroup()
                                .addContainerGap()
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(JRBMag, GroupLayout.Alignment.CENTER)
                                        .addComponent(jsmag))
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(JRBAzi, GroupLayout.Alignment.CENTER)
                                        .addComponent(jsazi))
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(JRBPol, GroupLayout.Alignment.CENTER)
                                        .addComponent(jspol))
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(JRBPdt, GroupLayout.Alignment.CENTER)
                                        .addComponent(jssum))
                                .addGroup(jPanelratioLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(JRBSum, GroupLayout.Alignment.CENTER)
                                        .addComponent(jspdt))
                        )
        );

        JRBMag.setText("Magnitude");
        JRBMag.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timemag += 1;
                if (timemag % 2 == 1) {
                    ismag = true;
                } else {
                    ismag = false;
                }
            }
        });
        JRBAzi.setText("Azimuth");
        JRBAzi.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timeazi += 1;
                if (timeazi % 2 == 1) {
                    isazi = true;
                } else {
                    isazi = false;
                }
            }
        });
        JRBPol.setText("Polar Angle");
        JRBPol.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timepol += 1;
                if (timepol % 2 == 1) {
                    ispol = true;
                } else {
                    ispol = false;
                }
            }
        });
        JRBPdt.setText("Product");
        JRBPdt.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timepdt += 1;
                if (timepdt % 2 == 1) {
                    ispdt = true;
                } else {
                    ispdt = false;
                }
            }
        });
        JRBSum.setText("Summation");
        JRBSum.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timesum += 1;
                if (timesum % 2 == 1) {
                    issum = true;
                } else {
                    issum = false;
                }
            }
        });

        jButtonHessianRun.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent ae) {
                String win = txtwinradius.getText();
                String map = txtmappingpower.getText();
                String alp = txtalpha.getText();
                String nul = txtnullCT.getText();
                boolean iswin = win.equals("") == false;
                boolean ismap = map.equals("") == false;
                boolean isalp = alp.equals("") == false;
                boolean isnul = nul.equals("") == false;

                if (nift.length != 0 && iswin && ismap && isalp && isnul) {
                    double[][][] nifti = util.convert2intArry(nift);
                    winradius = Integer.valueOf(win);
                    mappingpower = Integer.valueOf(map);
                    alpha = Integer.valueOf(alp);
                    nullCT = Integer.valueOf(nul);
                    for (int i = 0; i < 10/*nifti's.length*/; i++) {
                        Hessian_Deriche_3D_modified hd3m = new Hessian_Deriche_3D_modified(nifti[i], winradius, alpha, mappingpower, nullCT);
                        hd3m.Hessian_deriche_3D();
                        BufferedImage[] imset = hd3m.getBufferedImageSets();
                        mags.add(imset[0]);
                        azis.add(imset[1]);
                        pols.add(imset[2]);
                        sums.add(imset[3]);
                        pdts.add(imset[4]);
                    }
                    if (ismag == true) {
                        channelidxs.add(0);
                        hessianImgPanel hip = new hessianImgPanel(mags, width, height, crtchannel, wd);
                        channelspanel.add(hip);
                    }

                    if (isazi == true) {
                        channelidxs.add(1);
                        hessianImgPanel hip = new hessianImgPanel(azis, width, height, crtchannel, wd);
                        channelspanel.add(hip);
                    }

                    if (ispol == true) {
                        channelidxs.add(2);
                        hessianImgPanel hip = new hessianImgPanel(pols, width, height, crtchannel, wd);
                        channelspanel.add(hip);
                    }

                    if (issum == true) {
                        channelidxs.add(3);
                        hessianImgPanel hip = new hessianImgPanel(sums, width, height, crtchannel, wd);
                        channelspanel.add(hip);
                    }

                    if (ispdt == true) {
                        channelidxs.add(4);
                        hessianImgPanel hip = new hessianImgPanel(pdts, width, height, crtchannel, wd);
                        channelspanel.add(hip);
                    }

                    if (channelidxs.size() != 0) {
                        hessianImgPanel hip = channelspanel.get(crtchannel);
                        jSplitPaneHessian1.setBottomComponent(hip);
                        hip.setVisible(true);
                        jSplitPaneHessian1.setVisible(true);
                        isplayingchannel = true;
                    }

                } else {
                    //pop up a warning windows
                }
            }
        });

        hip.addMouseWheelListener(new MouseWheelListener() {
            @Override
            public void mouseWheelMoved(MouseWheelEvent mwe) {
                if (isplayingchannel == true) {

                    int dir = mwe.getWheelRotation();
                    // down
                    if (dir == 1) {
                        try {
                            if (channelpagenum <= mags.size() - 1) {
                                channelpagenum += 1;
                            }
                            if (crtchannel == 0) {
                                hip = new hessianImgPanel(mags, width, height, channelpagenum, wd);
                            } else if (crtchannel == 1) {
                                hip = new hessianImgPanel(azis, width, height, channelpagenum, wd);
                            } else if (crtchannel == 2) {
                                hip = new hessianImgPanel(pols, width, height, channelpagenum, wd);
                            } else if (crtchannel == 3) {
                                hip = new hessianImgPanel(sums, width, height, channelpagenum, wd);
                            } else if (crtchannel == 4) {
                                hip = new hessianImgPanel(pdts, width, height, channelpagenum, wd);
                            }

                            jSplitPane1.setRightComponent(hip);
                        } catch (Exception e) {
                        }
                    }

                    // up
                    if (dir == -1) {
                        try {
                            if (channelpagenum >= 0) {
                                channelpagenum -= 1;
                            }
                            if (crtchannel == 0) {
                                hip = new hessianImgPanel(mags, width, height, channelpagenum, wd);
                            } else if (crtchannel == 1) {
                                hip = new hessianImgPanel(azis, width, height, channelpagenum, wd);
                            } else if (crtchannel == 2) {
                                hip = new hessianImgPanel(pols, width, height, channelpagenum, wd);
                            } else if (crtchannel == 3) {
                                hip = new hessianImgPanel(sums, width, height, channelpagenum, wd);
                            } else if (crtchannel == 4) {
                                hip = new hessianImgPanel(pdts, width, height, channelpagenum, wd);
                            }

                            jSplitPane1.setRightComponent(hip);
                        } catch (Exception e) {
                        }
                    }

                }
            }
        });
    }

    /*
    * Basic Function of program
    * Status: under-developed
     */
    private void FunctionLayout() {

        box = new JComboBox(array);     
        box.setRenderer(rendrar);
        box.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                coloridx = (int) box.getSelectedItem();
                System.out.println("selected color " + coloridx);
            }

        });
        ImageIcon img = new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/SelectionLabel.png"));
        jButtonSelect.setIcon(img);
        jButtonSelect.setSize(32, 32);
        jButtonSelect.setPreferredSize(new Dimension(32, 32));
        jButtonSelect.setToolTipText("Select");
        jButtonSelect.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                clickpaint = true;

            }

        });

        jPanelmiddleworshop.add(jButtonSelect);
        jPanelmiddleworshop.add(box);
        jButtonsaveContours.setText("Active Incision Mode");
        jButtonStartFreeAnotation.setText("Active Anotation Mode");
        jPanelFreeAnnotation.add(jButtonsaveContours);

        //Nifti Folder Selection
        jButtondicoms.setText("Choose Nifti");
        jButtondicoms.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                JFileChooser chooser = new JFileChooser();
                chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                int returnVal = chooser.showOpenDialog(jButtondicoms);
                if (returnVal == JFileChooser.APPROVE_OPTION) {
                    NiftiFilePath = chooser.getSelectedFile().getAbsolutePath();
                    hasset = true;
                    String asd = NiftiFilePath;
                    dicomPath.setText(asd);
                    File files = new File(asd);
                    String[] a = files.list();
                    String[] dict = certainType(a);
                    niftifolder = dict;
                    listFileChooser.removeAll();
                    for (int i = 0; i < dict.length; i++) {
                        listFileChooser.add(dict[i]);
                    }
                }
            }
        });
        listFileChooser.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                int num = listFileChooser.getSelectedIndex();
                String SelectedNifti = util.CreatingPath(NiftiFilePath, niftifolder[num]);

                niftifile = new nifti(SelectedNifti);
                max = niftifile.getMax();
                min = niftifile.getMin();
                try {
                    nift = niftifile.toBufferedImageArr(max, min);
                    biggerNift = new BufferedImage[nift.length];
                    for (int i = 0; i < nift.length; i++) {
                        biggerNift[i] = util.resize(nift[i], 850, 800);
                    }
                    biggerniftis = new int[biggerNift.length][biggerNift[0].getWidth()][biggerNift[0].getHeight()];
                    biggerniftis = util.convert2realintArry(biggerNift);
                } catch (IOException ex) {
                    Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                    System.out.println("Reading error");
                }

                jimgpanels = new CustomImgPanel[nift.length];
                for (int i = 0; i < nift.length; i++) {
                    try {
                        jimgpanels[i] = new CustomImgPanel(850, 800, transparency, i, wd);
                    } catch (IOException ex) {
                        Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                    }
                }
                sp = new scrollablePanels(wd, jimgpanels);
                jSplitPane1.setRightComponent(sp);
                niftis = util.cvtdb3d2int3d(util.convert2intArry(nift));

                jSplitPane1.setRightComponent(sp);
                System.out.println("finished");

            }
        });

        //Mask Folder Selection
        jButtonMasks.setText("Choose Masks");
        jButtonMasks.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                JFileChooser chooser = new JFileChooser();
                chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
                int returnVal = chooser.showOpenDialog(jButtondicoms);
                if (returnVal == JFileChooser.APPROVE_OPTION) {
                    NiftiMaskPath = chooser.getSelectedFile().getAbsolutePath();
                    hasset = true;
                    String asd = NiftiMaskPath;
                    maskPath.setText(asd);
                    File filesmask = new File(asd);
                    String[] amask = filesmask.list();
                    String[] dictmask = certainType(amask);
                    maskfolder = dictmask;
                    listMaskChooser.removeAll();
                    for (int i = 0; i < dictmask.length; i++) {
                        listMaskChooser.add(dictmask[i]);
                    }

                }
            }
        });
        listMaskChooser.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                int num = listMaskChooser.getSelectedIndex();
                String SelectedNifti = util.CreatingPath(NiftiMaskPath, maskfolder[num]);

                maskfile = new nifti(SelectedNifti);
                try {
                    mask = maskfile.toBufferedImageArr(maskfile.getMax(), maskfile.getMin());
                    biggeMask = new BufferedImage[mask.length];
                    for (int i = 0; i < mask.length; i++) {
                        biggeMask[i] = util.resize(mask[i], 850, 800);
                    }
                    biggermasks = new int[biggeMask.length][biggeMask[0].getWidth()][biggeMask[0].getHeight()];
                    biggermasks = util.convert2realintArry(biggeMask);
                } catch (IOException ex) {
                    Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                    System.out.println("Reading error");
                }

                System.out.println("transparency is " + transparency);
                masks = util.cvtdb3d2int3d(util.convert2intArry(mask));

                jimgpanels = new CustomImgPanel[masks.length];
                for (int i = 0; i < masks.length; i++) {
//                    if(i==10)
//                        break;
                    /*asdfasfdjadlfasldjf*/
                    try {
                        jimgpanels[i] = new CustomImgPanel(850, 800, transparency, i, wd);
                        System.out.println("this is " + i + " generated");
                    } catch (IOException ex) {
                        Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                    }
                }
                sp = new scrollablePanels(wd, jimgpanels);
                jSplitPane1.setRightComponent(sp);
                System.out.println("masked");
            }
        });

//        //set for jSliderMaxWindowsLvl
//        jSliderMaxWindowsLvl.addChangeListener(new ChangeListener() {
//            @Override
//            public void stateChanged(ChangeEvent ce) {
//                if (hasset == true) {
//                    jSliderMaxWindowsLvl = new JSlider((int) max, (int) min);
//                    System.out.println("max was " + max);
//                    max = jSliderMaxWindowsLvl.getValue();
//                    System.out.println("max is " + max);
//                    jSpinnerMaxWindowsLvl.setValue(max);
//                    try {
//                        nift = niftifile.toBufferedImageArr((int) max, (int) min);
//                    } catch (IOException ex) {
//                        System.out.println("error on JSliderMaxWindowsLvl");
//                        Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
//                    }
//                    jimgpanel = new CustomImgPanel(850, 800, transparency, pagenum, wd);
//                    jimgpanels = new CustomImgPanel[nift.length];
//                    for (int i = 0; i < nift.length; i++) {
////                        jimgpanels[i] = new CustomImgPanel(850, 800, transparency, i, wd);
//                    }
////                    sp = new scrollablePanels(wd, jimgpanels);
////                    jSplitPane1.setRightComponent(sp);
//                }
//            }
//        });
//        //set for jSliderMinWindowLvl
//        jSliderMinWindowsLvl.addChangeListener(new ChangeListener() {
//            @Override
//            public void stateChanged(ChangeEvent ce) {
//                if (hasset == true) {
//                    jSliderMinWindowsLvl = new JSlider((int) max, (int) min);
//                    min = jSliderMinWindowsLvl.getValue();
//                    jSpinnerMaxWindowsLvl.setValue(min);
//                    try {
//                        nift = niftifile.toBufferedImageArr((int) max, (int) min);
//                    } catch (IOException ex) {
//                        System.out.println("error on jSliderMinWindowsLvl");
//                        Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
//                    }
////                    jimgpanel = new CustomImgPanel(850, 800, transparency, pagenum, wd);
//
////                    jSplitPane1.setRightComponent(jimgpanel);
//                }
//            }
//        });
        GroupLayout jPanelTopMenuToolLayout = new GroupLayout(jPanelTopMenuTool);

        jPanelTopMenuTool.setLayout(jPanelTopMenuToolLayout);
        jPanelTopMenuToolLayout.setHorizontalGroup(
                jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelTopMenuToolLayout.createSequentialGroup()
                                .addGroup(jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(maxlvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(minlvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(transparencylvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                .addGroup(jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(jSliderMaxWindowsLvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(jSliderMinWindowsLvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(jSliderTransparency, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                .addGroup(jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(jSpinnerMaxWindowsLvl)
                                        .addComponent(jSpinnerMinWindowsLvl)
                                        .addComponent(jSpinnerTransparency))
                        )
        );
        jPanelTopMenuToolLayout.setVerticalGroup(
                jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelTopMenuToolLayout.createSequentialGroup()
                                .addContainerGap()
                                .addGroup(jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(jSpinnerMaxWindowsLvl)
                                        .addComponent(jSliderMaxWindowsLvl)
                                        .addComponent(maxlvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                                .addGroup(jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(jSliderMinWindowsLvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(jSpinnerMinWindowsLvl, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                                        .addComponent(minlvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                                .addGroup(jPanelTopMenuToolLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(jSliderTransparency, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(jSpinnerTransparency, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                                        .addComponent(transparencylvl, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );

        GroupLayout jPanelBotMenuToolLayout = new GroupLayout(jPanelBotMenuTool);
        jPanelBotMenuTool.setLayout(jPanelBotMenuToolLayout);
        jPanelBotMenuToolLayout.setHorizontalGroup(
                jPanelBotMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGap(0, 89, Short.MAX_VALUE)
        );
        jPanelBotMenuToolLayout.setVerticalGroup(
                jPanelBotMenuToolLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGap(0, 621, Short.MAX_VALUE)
        );

    }

    private void LevelSetWindow() {
        JRBISALLlevelset.setText("Apply All?");
        JRBISALLlevelset.addChangeListener(new ChangeListener() {
            @Override
            public void stateChanged(ChangeEvent e) {
                isapplyallLevelset = true;
            }
        });

        txtiternum.setPreferredSize(new Dimension(100, 30));
        txtlambdal.setPreferredSize(new Dimension(100, 30));
        txtnu.setPreferredSize(new Dimension(100, 30));
        txtmu.setPreferredSize(new Dimension(100, 30));
        txttimestep.setPreferredSize(new Dimension(100, 30));
        txtepsilon.setPreferredSize(new Dimension(100, 30));
        jButtonDoLevelset.setPreferredSize(new Dimension(100, 30));
        jButtonDoLevelset.setText("Apply");

        GroupLayout jPanelLevelsetLayout = new GroupLayout(jPanelLevelset);
        jPanelLevelset.setLayout(jPanelLevelsetLayout);
        jPanelLevelsetLayout.setHorizontalGroup(
                jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelLevelsetLayout.createSequentialGroup()
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(lbliternum)
                                        .addComponent(lbllambdal)
                                        .addComponent(lblnu)
                                        .addComponent(lblmu)
                                        .addComponent(lbltimestep)
                                        .addComponent(lblepsilon)
                                        .addComponent(jButtonDoLevelset))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(txtiternum)
                                        .addComponent(txtlambdal)
                                        .addComponent(txtnu)
                                        .addComponent(txtmu)
                                        .addComponent(txttimestep)
                                        .addComponent(txtepsilon)
                                        .addComponent(JRBISALLlevelset))
                        )
        );
        jPanelLevelsetLayout.setVerticalGroup(
                jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelLevelsetLayout.createSequentialGroup()
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lbliternum, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtiternum))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lbllambdal, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtlambdal))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblnu, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtnu))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblmu, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtmu))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lbltimestep, GroupLayout.Alignment.CENTER)
                                        .addComponent(txttimestep))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblepsilon, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtepsilon))
                                .addGroup(jPanelLevelsetLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(jButtonDoLevelset, GroupLayout.Alignment.CENTER)
                                        .addComponent(JRBISALLlevelset))
                        )
        );
    }

    private void WatershedWindow() {
        JRBISAll.setText("Apply All?");
        JRBISAll.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                isapplyall = true;
            }
        });
        txtwtsdhighthreshold.setPreferredSize(new Dimension(100, 30));
        txtwtsdlowthreshold.setPreferredSize(new Dimension(100, 30));
        jButtonDoWatershed.setPreferredSize(new Dimension(100, 50));
        jButtonDoWatershed.setText("Apply");
        jButtonDoWatershed.addActionListener(new ActionListener() {

            @Override
            public void actionPerformed(ActionEvent e) {
                if (!txtwtsdhighthreshold.getText().isEmpty() || !txtwtsdlowthreshold.getText().isEmpty() || !txtklengthx.getText().isEmpty() || !txtklengthy.getText().isEmpty()) {
                    System.out.println("Entered 1068");
                    klengthx = Integer.valueOf(txtklengthx.getText());
                    klengthy = Integer.valueOf(txtklengthy.getText());
                    highthreshold = Integer.valueOf(txtwtsdhighthreshold.getText());
                    lowthreshold = Integer.valueOf(txtwtsdlowthreshold.getText());
                    if (isapplyall == false) {
                        try {
                            Mat mt = util.bufferToMartix(nift[pagenum]);
                            Watershed wtsd = new Watershed(klengthx, klengthy, highthreshold, lowthreshold, mt, jimgpanels[pagenum]);
                            fromwtsd = new Vector<JLabel[]>();
                            coodinates = new Vector<Point>();
                            msksizes = new Vector<int[]>();

                            wtsd.run();

                            Vector<Mask> msks = wtsd.getMasks();
                            for (int i = 0; i < msks.size(); i++) {
                                System.out.println("this is " + i);
                                Mask mk = msks.get(i);
                                fromwtsd.add(mk.makeMask(colorchoice[coloridx]));
                                coodinates.add(mk.getLeftTopCorner());
                                int arr[] = {mk.nw, mk.nh};
                                msksizes.add(arr);
//                                mk.saveResizedmask("D:\\exp\\msk_1\\a_" + i + ".png");
                            }

                            for (int i = 0; i < fromwtsd.size(); i++) {
                                JLabel jlb1 = fromwtsd.get(i)[0];
                                int x = coodinates.get(i).x;
                                int y = coodinates.get(i).y;
                                int sx = msksizes.get(i)[0];
                                int sy = msksizes.get(i)[1];
                                jlb1.setLocation(x, y);
//                                sp.cips[pagenum].saveImage("D:\\exp\\asd\\" + i + ".png");
                                jimgpanels[pagenum].add(jlb1);
                                sp.setVisible(false);
                                sp.remove(sp.cips[pagenum]);
                                sp.add(sp.cips[wd.pagenum], BorderLayout.CENTER);
                                sp.setVisible(true);

                                /*below adding actionlisteners*/
                                jlb1.addMouseMotionListener(new MouseMotionListener() {
                                    @Override
                                    public void mouseDragged(MouseEvent e) {

                                    }

                                    @Override
                                    public void mouseMoved(MouseEvent e) {

                                    }

                                });

                            }

                        } catch (Exception ex) {
                            Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                        }
                    } else {
                        for (int k = 0; k < nift.length; k++) {
                            try {
                                Mat mt = util.bufferToMartix(nift[k]);
                                Watershed wtsd = new Watershed(klengthx, klengthy, highthreshold, lowthreshold, mt, jimgpanels[k]);
                                fromwtsd = new Vector<JLabel[]>();
                                coodinates = new Vector<Point>();
                                msksizes = new Vector<int[]>();

                                wtsd.run();

                                Vector<Mask> msks = wtsd.getMasks();
                                for (int i = 0; i < msks.size(); i++) {
                                    System.out.println("this is " + i);
                                    Mask mk = msks.get(i);
                                    fromwtsd.add(mk.makeMask(colorchoice[coloridx]));
                                    coodinates.add(mk.getLeftTopCorner());
                                    int arr[] = {mk.nw, mk.nh};
                                    msksizes.add(arr);
//                                mk.saveResizedmask("D:\\exp\\msk_1\\a_" + i + ".png");
                                }

                                for (int i = 0; i < fromwtsd.size(); i++) {
                                    JLabel jlb1 = fromwtsd.get(i)[0];
                                    int x = coodinates.get(i).x;
                                    int y = coodinates.get(i).y;
                                    int sx = msksizes.get(i)[0];
                                    int sy = msksizes.get(i)[1];
                                    jlb1.setLocation(x, y);
//                                sp.cips[pagenum].saveImage("D:\\exp\\asd\\" + i + ".png");
                                    jimgpanels[k].add(jlb1);
                                    sp.setVisible(false);
                                    sp.remove(sp.cips[k]);
                                    wd.pagenum=k;
                                    sp.add(sp.cips[wd.pagenum], BorderLayout.CENTER);
                                    sp.setVisible(true);

                                    /*below adding actionlisteners*/
                                    jlb1.addMouseMotionListener(new MouseMotionListener() {
                                        @Override
                                        public void mouseDragged(MouseEvent e) {

                                        }

                                        @Override
                                        public void mouseMoved(MouseEvent e) {

                                        }

                                    });

                                }

                            } catch (Exception ex) {
                                Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                            }
                        }
                    }

                } else {
                    WarningWindow("error!!! not enough info, please fill all blanks");
                }
            }
        });

        GroupLayout jPanelWaterLayout = new GroupLayout(jPanelWatershed);
        jPanelWatershed.setLayout(jPanelWaterLayout);
        jPanelWaterLayout.setHorizontalGroup(
                jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelWaterLayout.createSequentialGroup()
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(lblwtsdhighthreshold)
                                        .addComponent(lblwtsdlowthreshold)
                                        .addComponent(lblklengthx)
                                        .addComponent(lblklengthy)
                                        .addComponent(jButtonDoWatershed))
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(txtwtsdhighthreshold)
                                        .addComponent(txtwtsdlowthreshold)
                                        .addComponent(txtklengthx)
                                        .addComponent(txtklengthy)
                                        .addComponent(JRBISAll))
                        )
        );
        jPanelWaterLayout.setVerticalGroup(
                jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelWaterLayout.createSequentialGroup()
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblwtsdhighthreshold, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtwtsdhighthreshold))
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblwtsdlowthreshold, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtwtsdlowthreshold))
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblklengthx, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtklengthx))
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblklengthy, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtklengthy))
                                .addGroup(jPanelWaterLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(jButtonDoWatershed, GroupLayout.Alignment.CENTER)
                                        .addComponent(JRBISAll))
                        )
        );

    }

    private void WarningWindow(String warning) {
        jPanelWarning.setLayout(new BorderLayout());
        lblwarning = new JLabel(warning);
        jPanelWarning.add(lblwarning, BorderLayout.CENTER);
        jFrameWarning.add(jPanelWarning);
        jFrameWarning.setSize(new Dimension(500, 300));
        jFrameWarning.setVisible(true);
    }

    /*
    * Basic Layout of entire JFrame
    * Status: finished
     */
    private void BasicLayout() {

        maxlvl.setText("Threshold");
        minlvl.setText("Window/Level");
        transparencylvl.setText("Opaque");

        initial.setBackground(Color.BLACK);
        initial.setSize(850, 800);

        this.getContentPane().add(jSplitPane1);
        this.addMouseWheelListener(this);

        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);

        jSplitPane1.setLeftComponent(distractTab);
        jSplitPane1.setRightComponent(initial);

        jSplitPane3.setOrientation(JSplitPane.VERTICAL_SPLIT);
        jSplitPane3.setBottomComponent(jSplitPane6);
        jSplitPane3.setTopComponent(jPanelTopMenuTool);

        jSplitPane4.setOrientation(JSplitPane.VERTICAL_SPLIT);
        jSplitPane4.setTopComponent(jPanellisttop);
        jSplitPane4.setBottomComponent(jSplitPane5);

        jSplitPane5.setOrientation(JSplitPane.VERTICAL_SPLIT);
        jSplitPane5.setTopComponent(listFileChooser);
        jSplitPane5.setBottomComponent(listMaskChooser);

        jSplitPane6.setOrientation(JSplitPane.VERTICAL_SPLIT);
        jSplitPane6.setTopComponent(jPanelmiddleworshop);
        jSplitPane6.setBottomComponent(botMenu);

        distractTab.add("Files", jSplitPane4);
        distractTab.add("Tools", jSplitPane3);
        distractTab.setBorder(new LineBorder(Color.black, 1));

        jSplitPane1.setDividerLocation(285);
        jSplitPane1.setBorder(new LineBorder(Color.black, 1));
        jSplitPane1.setEnabled(false);
        jSplitPane3.setDividerLocation(120);
        jSplitPane3.setEnabled(false);
        jSplitPane4.setDividerLocation(83);
        jSplitPane4.setEnabled(false);
        jSplitPane5.setDividerLocation(330);
        jSplitPane5.setEnabled(false);
        jSplitPane6.setDividerLocation(230);
        jSplitPane6.setBorder(new LineBorder(Color.black, 1));
        jSplitPane6.setEnabled(false);

        maskPath.setPreferredSize(new Dimension(150, 30));
        maskPath.setEditable(false);
        dicomPath.setPreferredSize(new Dimension(150, 30));
        dicomPath.setEditable(false);

        GroupLayout jPanellistTopLayout = new GroupLayout(jPanellisttop);
        jPanellisttop.setLayout(jPanellistTopLayout);
        jPanellistTopLayout.setHorizontalGroup(
                jPanellistTopLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanellistTopLayout.createSequentialGroup()
                                .addGroup(jPanellistTopLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(dicomPath, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(maskPath, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                .addGroup(jPanellistTopLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(jButtondicoms, GroupLayout.DEFAULT_SIZE, 100, Short.MAX_VALUE)
                                        .addComponent(jButtonMasks)))
        );

        jPanellistTopLayout.setVerticalGroup(
                jPanellistTopLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanellistTopLayout.createSequentialGroup()
                                .addContainerGap()
                                .addGroup(jPanellistTopLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(dicomPath, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                                        .addComponent(jButtondicoms, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                                .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                                .addGroup(jPanellistTopLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(maskPath, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                                        .addComponent(jButtonMasks, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
                                .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        );
        jButtonEndAnnote.setText("End");

    }

    /*
    * Segmentation part of panel
    * Status: finished
     */
    private void segmentationpart() {
        jPanelHessianMethod.add(jButtonReadyHessianChannel, BorderLayout.SOUTH);

        ImageIcon Hes = new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/HessianButton.png"));
        jButtonReadyHessianChannel.setIcon(Hes);
        jButtonReadyHessianChannel.setToolTipText("Select Hessian domain(s)");
        jButtonReadyHessianChannel.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent ae) {
                jFrameHessian.setLocation(100, 50);
                jFrameHessian.setSize(800, 700);
                jFrameHessian.setModalExclusionType(Dialog.ModalExclusionType.NO_EXCLUDE);
                jFrameHessian.setVisible(true);
            }
        });

        txtretreatratio.setPreferredSize(new Dimension(100, 30));
        txtfilter.setPreferredSize(new Dimension(100, 30));
        txtthresholdset.setPreferredSize(new Dimension(100, 30));
        jButtonApply.setPreferredSize(new Dimension(100, 50));
        jButtonApply.setText("Apply");

        GroupLayout jPanelHessLayout = new GroupLayout(jPanelHessianMethod);
        jPanelHessianMethod.setLayout(jPanelHessLayout);
        jPanelHessLayout.setHorizontalGroup(
                jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelHessLayout.createSequentialGroup()
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(lblretreatratio)
                                        .addComponent(lblfilter)
                                        .addComponent(lblthresholdset)
                                        .addComponent(lblsegtime)
                                        .addComponent(jButtonReadyHessianChannel))
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                        .addComponent(txtretreatratio)
                                        .addComponent(txtfilter)
                                        .addComponent(txtthresholdset)
                                        .addComponent(txtsegtime)
                                        .addComponent(jButtonApply))
                        )
        );
        jPanelHessLayout.setVerticalGroup(
                jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(jPanelHessLayout.createSequentialGroup()
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblretreatratio, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtretreatratio))
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblfilter, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtfilter))
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblthresholdset, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtthresholdset))
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(lblsegtime, GroupLayout.Alignment.CENTER)
                                        .addComponent(txtsegtime))
                                .addGroup(jPanelHessLayout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                                        .addComponent(jButtonReadyHessianChannel, GroupLayout.Alignment.CENTER)
                                        .addComponent(jButtonApply))
                        )
        );

        HessianContainer = new JScrollPane(jPanelHessianMethod);

//        botMenu.addTab("Hessian", HessianContainer);
        botMenu.addTab("Annote", jPanelFreeAnnotation);
        botMenu.addTab("Watershed", jPanelWatershed);
        botMenu.addTab("Levelset", jPanelLevelset);

        GroupLayout layout = new GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addComponent(jSplitPane1, GroupLayout.DEFAULT_SIZE, 1143, Short.MAX_VALUE)
        );
        layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addComponent(jSplitPane1, GroupLayout.DEFAULT_SIZE, 715, Short.MAX_VALUE)
        );

        jButtonApply.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent ae) {
                if (hasset == true) {

                    String rr = txtretreatratio.getText();
                    String ft = txtfilter.getText();
                    String seg = txtsegtime.getText();
                    String tss = util.addcoma(txtthresholdset.getText());

                    if (rr.equals("") != true && ft.equals("") != true && tss.equals("") != true) {
                        retreatratio = Double.valueOf(rr);
                        filter = Integer.valueOf(ft);
                        segtime = (int) Math.pow(2, Integer.valueOf(seg));
                        //format "[n1,n2,n3,...]"
                        for (int i = 1; i < tss.length() - 1; i++) {
                            int startidx = i;
                            for (int j = i; j < tss.length() - 1; j++) {
                                if (tss.charAt(j) == ',') {
                                    String sub = tss.substring(startidx, j);
                                    int thresh = Integer.valueOf(sub);
                                    thresholdset.add(thresh);
                                    i = j;
                                    break;
                                }
                            }
                        }

                        //currently is mags
                        int[][][] nif = util.cvt2int3d(mags);
                        for (int k = 0; k < thresholdset.size() - 1; k++) {
                            Vector<Vector<Vector<int[]>>> threshold = new Vector();
                            for (int i = 0; i < nif.length; i++) {
                                try {
                                    edge_detection ed = new edge_detection(nif[i], thresholdset.get(i), thresholdset.get(i + 1), retreatratio, segtime);
                                    ed.segpic();
                                    BufferedImage cont = ed.getfinalbufferedcontour();
                                    Find_connection fc = new Find_connection(cont, filter);

                                    threshold.add(fc.find_connection());

                                } catch (Exception ex) {
                                    Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                                }
                            }
                            points.add(threshold);
                        }
                    }
                } else {
                    System.out.println("empty!");
                }
            }

        });
    }

    /*find .nii or .gz format files under a folder(fully-developed)
        status: fully-developed
     */
    public String[] certainType(String[] address) {
        Vector<String> add = new Vector();
        for (int i = 0; i < address.length; i++) {
            if (address[i].subSequence(address[i].length() - 3, address[i].length()).equals("nii")) {
                add.add(address[i]);
            } else if (address[i].subSequence(address[i].length() - 2, address[i].length()).equals("gz")) {
                add.add(address[i]);
            }
        }

        String[] arr = new String[add.size()];
        for (int i = 0; i < arr.length; i++) {
            arr[i] = add.get(i);
        }

        return arr;
    }


    /*main method(fully-developed)
        dont need to worry about it
     */
    public static void main(String args[]) {
        try {
            for (UIManager.LookAndFeelInfo info : UIManager.getInstalledLookAndFeels()) {
                if ("Nimbus".equals(info.getName())) {
                    UIManager.setLookAndFeel(info.getClassName());
                }
            }
        } catch (ClassNotFoundException ex) {
            java.util.logging.Logger.getLogger(WindowDesign.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (InstantiationException ex) {
            java.util.logging.Logger.getLogger(WindowDesign.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (IllegalAccessException ex) {
            java.util.logging.Logger.getLogger(WindowDesign.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (UnsupportedLookAndFeelException ex) {
            java.util.logging.Logger.getLogger(WindowDesign.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        }

        /* Create and display the form */
        EventQueue.invokeLater(new Runnable() {
            public void run() {
                try {
                    new WindowDesign().setVisible(true);
                } catch (IOException ex) {
                    Logger.getLogger(WindowDesign.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
        });
    }

    /*
    * turn to transparent color
     */
    public void turncolor(int colorIndexs) throws IOException {
        Vector<Point> colored = new Vector<Point>();
        BufferedImage bf = nift[pagenum];
        BufferedImage bfi = new BufferedImage(bf.getWidth(), bf.getHeight(), bf.TYPE_INT_RGB);
        Polygon contours = new Polygon();
        for (Point p : pointset) {
//            System.out.print("(" + p.x + "," + p.y + ") ");
            contours.addPoint(p.x, p.y);
        }
        int[][] niftii = niftis[pagenum];
        for (int i = 0; i < bf.getWidth(); i++) {
            for (int j = 0; j < bf.getHeight(); j++) {
                colored.add(new Point(i, j));

            }
        }
        msk = new Mask(colored, jimgpanels[pagenum], coloridx);
        nift[pagenum] = msk.getResizedMask();;
    }


    /*for mouse wheel movement
    Status: finished
     */
    @Override
    public void mouseWheelMoved(MouseWheelEvent mwe) {
        if (hasset == true) {
            int dir = mwe.getWheelRotation();
            // down
            if (dir == 1) {
                try {
                    if (wd.pagenum != wd.nift.length - 1) {
                        sp.setVisible(false);
                        sp.remove(sp.cips[pagenum]);
                        pagenum += 1;
                    }
                    sp.sb.setValue(pagenum);
                    sp.add(sp.cips[wd.pagenum], BorderLayout.CENTER);
                    sp.setVisible(true);
                    System.out.println("I am in " + pagenum + " when down");
                    isnxtpage = true;
                } catch (Exception e) {
                }
            }

            // up
            if (dir == -1) {
                try {
                    if (pagenum != 0) {
                        sp.setVisible(false);
                        sp.remove(sp.cips[pagenum]);
                        pagenum -= 1;
                    }
                    sp.sb.setValue(pagenum);
                    sp.add(sp.cips[wd.pagenum], BorderLayout.CENTER);
                    sp.setVisible(true);
                    System.out.println("I am in " + pagenum + " when up");
                    isnxtpage = true;
                } catch (Exception e) {
                }
            }
        }
    }

    /*
    *  Inner class ComboBoxRenderar
    *  Status: finished
    *  create a pair of combobox
     */
    public class ComboBoxRenderar extends JLabel implements ListCellRenderer {

        @Override
        public Component getListCellRendererComponent(JList list, Object value, int index, boolean isSelected, boolean cellHasFocus) {
            int offset = ((Integer) value).intValue();

            ImageIcon icon = imageIcon[offset];
            String name = names[offset];

            if (offset != 0) {
                coloridx = offset;
            }

            setIcon(icon);
            setText(name);

            return this;
        }

    }

    protected Scrollbar sidescroll;
    protected JFrame jFrameHessian, jFrameWarning;
    protected hessianImgPanel hip;
    protected JLabel initial, maxlvl, minlvl, transparencylvl, lblCurrentPics, lblwinradius, lblmappingpower, lblalpha, lblnullCT, lblthresholdset, lblretreatratio, lblfilter, lblsegtime, lblwtsdhighthreshold, lblwtsdlowthreshold, lblwarning, lblklengthx, lblklengthy, lbliternum, lbllambdal, lblnu, lblmu, lbltimestep, lblepsilon,jSpinnerMaxWindowsLvl, jSpinnerMinWindowsLvl,jSpinnerTransparency;
    protected JPanel jPanelBotMenuTool, jPanellisttop, jPanelTopMenuTool, jPanelmiddleworshop, jPanelFreeAnnotation, jPanelHessianMethod, jPanelImgDisplay, jPanelHessianImgAction, jPanelRunOption, jPanelHessianRadioSpin, jPanelWatershed, jPanelWarning, jPanelLevelset;
    protected JScrollPane HessianContainer, jPanelHessianRadioButtons;
    protected RangeSlider jSliderMaxWindowsLvl, jSliderMinWindowsLvl;
    protected JSlider jSliderTransparency;
    protected JSpinner jsmag, jsazi, jspol, jssum, jspdt;
    protected JSplitPane jSplitPane1, jSplitPane3, jSplitPane4, jSplitPane5, jSplitPane6, jSplitPaneHessian1, jSplitPaneHessian2, jSplitPaneHessian3;
    protected List listFileChooser, listMaskChooser;
    protected JButton jButtonMasks, jButtondicoms, jButtonsaveContours, jButtonStartFreeAnotation, jButtonReadyHessianChannel, jButtonSelect, jButtonHessianRight, jButtonHessianLeft, jButtonHessianRun, jButtonHessianShow, jButtonApply, jButtonEndAnnote, jButtonClearLabel, jButttonDeleteSelectedLabel, jButtonDoWatershed, jButtonDoLevelset, jButtonDeleteContour;
    protected JCheckBox JRBMag, JRBAzi, JRBPol, JRBPdt, JRBSum, JRBISAll, JRBISALLlevelset;
    protected JTextField maskPath, dicomPath, txtwinradius, txtmappingpower, txtalpha, txtnullCT, txtthresholdset, txtretreatratio, txtfilter, txtsegtime, txtwtsdhighthreshold, txtwtsdlowthreshold, txtklengthx, txtklengthy, txtiternum, txtlambdal, txtnu, txtmu, txttimestep, txtepsilon;
    protected String NiftiFilePath, NiftiMaskPath;
    protected nifti niftifile, maskfile, savedmaskfile;
    protected JTabbedPane botMenu, distractTab;
    protected String[] niftifolder, maskfolder;
    protected double max, min, alpha;
    protected ComboBoxRenderar rendrar;
    public int startX, startY, endX, endY, firstX, firstY, coloridx, winradius, mappingpower, nullCT, totalnum, klengthx, klengthy, highthreshold, lowthreshold;
    protected JComboBox box;
    protected int[][][] niftis, masks;
    protected int[][][] biggerniftis, biggermasks;
    protected Mask msk;
    public Vector<Point> pointset = new Vector(), coodinates;
    public Utility util = new Utility();
    public scrollablePanels sp;
    public Vector<JLabel[]> contours, fromwtsd;
    public Vector<int[]> msksizes;

    //Hessian Windows
    public String channel[] = {"Magnitude Channel", "Azimuth Channel", "Polar Angle Channel", "Summation Channel", "Product Channel"};
    public Vector<Integer> channelidxs = new Vector(), thresholdset = new Vector();

    //merg has no thing yet!
    public Vector<BufferedImage> mags = new Vector(), azis = new Vector(), pols = new Vector(), sums = new Vector(), pdts = new Vector(), merg = new Vector(), finalcontours = new Vector();
    protected Vector<hessianImgPanel> channelspanel = new Vector();
    //Outermost represents total img(nifiti's length), then its the total threshold for each(threshold's length), then its the total contours, and int[] is the point
    protected Vector<Vector<Vector<Vector<int[]>>>> points = new Vector();

    //color labels
    protected Integer array[] = {0, 1, 2, 3, 4, 5, 6};
    protected ImageIcon imageIcon[] = {new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/NoLabel.png")), new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/RedLabel.png")), new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/CyanLabel.png")), new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/YellowLabel.png")), new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/GreenLabel.png")), new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/BlueLabel.png")), new ImageIcon(WindowDesign.class.getResource("/Contours/ImageLabels/VioletLabel.png"))};
    protected String names[] = {"No Label", "Label 1", "Label 2", "Label 3", "Label 4", "Label 5", "Label 6"};

    protected CustomImgPanel[] jimgpanels;
    public Vector<Vector<Point>> contourset = new Vector();
    public Color colorchoice[] = {Color.BLACK, Color.RED, Color.CYAN, Color.YELLOW, Color.GREEN, Color.BLUE, Color.PINK};
    protected float transparency = 0.2f;
    public boolean isfirst = true, started = false, hasset = false, ismag = false, isazi = false, ispol = false, ispdt = false, issum = false, ishybrid = false, isnxtpage = true, isplayingchannel = false, isapplyall = false, clickpaint = false, isapplyallLevelset = false;
    public int timemag = 0, timeazi = 0, timepol = 0, timepdt = 0, timesum = 0, pagenum = 0, channelpagenum = 0, crtchannel = 0, filter = 0, segtime = 0, clicktime = 0;
    protected double retreatratio = 0.5;
    public WindowDesign wd = this;
    public BufferedImage[] nift = new BufferedImage[0], mask = new BufferedImage[0], biggerNift = new BufferedImage[0], biggeMask = new BufferedImage[0];
}
