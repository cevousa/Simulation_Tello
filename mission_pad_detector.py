#!/usr/bin/env python3
"""
Mission Pad Detector - ปรับปรุงแล้ว
ตรวจจับ Mission Pad โดยการเปรียบเทียบรูปภาพ
"""

import cv2
import numpy as np
import os
import time
from datetime import datetime
from skimage import metrics
from skimage.transform import resize
from skimage.color import rgb2gray
from skimage.feature import match_template
import glob

class MissionPadDetector:
    def __init__(self, template_folder="mission_pad_templates", threshold=0.15):  # ลด threshold
        """
        เริ่มต้น Mission Pad Detector
        
        Args:
            template_folder (str): โฟลเดอร์ที่เก็บรูปภาพ template
            threshold (float): ค่าเกณฑ์สำหรับการตรวจจับ (ลดลงเหลือ 0.15)
        """
        self.template_folder = template_folder
        self.threshold = threshold
        self.templates = {}
        self.template_info = {}
        
        # โหลด templates
        self._load_templates()
        
        print(f"✅ MissionPadDetector initialized with threshold: {threshold}")
        print(f"📁 Templates loaded: {len(self.templates)} templates")
    
    def _load_templates(self):
        """โหลดรูปภาพ template ทั้งหมดจากโฟลเดอร์"""
        if not os.path.exists(self.template_folder):
            print(f"❌ Template folder not found: {self.template_folder}")
            return
        
        print(f"🔍 Loading templates from: {self.template_folder}")
        
        # ค้นหาไฟล์ในโฟลเดอร์และโฟลเดอร์ย่อย
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
        template_files = []
        
        for ext in image_extensions:
            # ค้นหาในโฟลเดอร์หลัก
            template_files.extend(glob.glob(os.path.join(self.template_folder, ext)))
            # ค้นหาในโฟลเดอร์ย่อย
            template_files.extend(glob.glob(os.path.join(self.template_folder, '**', ext), recursive=True))
        
        for template_path in template_files:
            try:
                # อ่านรูปภาพ
                template_img = cv2.imread(template_path)
                if template_img is None:
                    print(f"⚠️ Cannot read template: {template_path}")
                    continue
                
                # แปลงเป็น grayscale
                template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
                
                # หาเลข ID จากชื่อไฟล์หรือโฟลเดอร์
                template_id = self._extract_id_from_path(template_path)
                
                if template_id is not None:
                    # ปรับขนาดให้เหมาะสม
                    template_resized = cv2.resize(template_gray, (200, 200))
                    
                    self.templates[template_id] = template_resized
                    self.template_info[template_id] = {
                        'path': template_path,
                        'original_size': template_img.shape[:2],
                        'processed_size': template_resized.shape
                    }
                    
                    print(f"✅ Loaded template {template_id}: {template_path}")
                else:
                    print(f"⚠️ Cannot extract ID from: {template_path}")
                    
            except Exception as e:
                print(f"❌ Error loading template {template_path}: {e}")
        
        print(f"📊 Total templates loaded: {len(self.templates)}")
    
    def _extract_id_from_path(self, path):
        """แยกเลข ID จาก path ของไฟล์"""
        # ตัวอย่าง: mission_pad_templates/number_1/missionpad_1.png
        # หรือ: mission_pad_templates/missionpad_1.png
        
        # ลองหาจากชื่อโฟลเดอร์
        folder_name = os.path.basename(os.path.dirname(path))
        if 'number_' in folder_name:
            try:
                return int(folder_name.split('_')[1])
            except:
                pass
        
        # ลองหาจากชื่อไฟล์
        filename = os.path.basename(path)
        
        # ลองหาตัวเลขจากชื่อไฟล์
        import re
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[0])
        
        return None
    
    def detect_mission_pad(self, image_path):
        """
        ตรวจจับ Mission Pad จากรูปภาพ
        
        Args:
            image_path (str): path ของรูปภาพที่ต้องการตรวจจับ
            
        Returns:
            dict: ข้อมูลการตรวจจับ หรือ None ถ้าไม่พบ
        """
        if not self.templates:
            print("❌ No templates loaded")
            return None
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return None
        
        try:
            # อ่านรูปภาพ
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ Cannot read image: {image_path}")
                return None
            
            # แปลงเป็น grayscale
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # ปรับขนาดให้เหมาะสม
            image_resized = cv2.resize(image_gray, (200, 200))
            
            print(f"🔍 Comparing with templates...")
            
            best_match = None
            best_score = 0
            
            for template_id, template in self.templates.items():
                # คำนวณ similarity หลายวิธี
                scores = self._calculate_similarity(image_resized, template)
                
                # ใช้ค่า combined score
                combined_score = scores['combined']
                
                print(f"  Template {template_id}: {combined_score:.3f}")
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        'id': template_id,
                        'confidence': combined_score,
                        'scores': scores,
                        'template_info': self.template_info[template_id]
                    }
            
            # ตรวจสอบว่าผ่านเกณฑ์หรือไม่
            if best_score >= self.threshold:
                print(f"✅ Mission pad detected: ID {best_match['id']} (confidence: {best_score:.3f})")
                return best_match
            else:
                print(f"❌ No mission pad detected (best: {best_score:.3f}, threshold: {self.threshold})")
                return None
                
        except Exception as e:
            print(f"❌ Detection error: {e}")
            return None
    
    def _calculate_similarity(self, image, template):
        """คำนวณ similarity ระหว่างรูปภาพ 2 รูป"""
        try:
            # 1. Template Matching
            result = match_template(image, template)
            template_score = np.max(result)
            
            # 2. SSIM (Structural Similarity Index)
            ssim_score = metrics.structural_similarity(image, template)
            
            # 3. Normalized Cross Correlation
            norm_image = (image - np.mean(image)) / np.std(image)
            norm_template = (template - np.mean(template)) / np.std(template)
            ncc_score = np.mean(norm_image * norm_template)
            
            # 4. Histogram Correlation
            hist1 = cv2.calcHist([image], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([template], [0], None, [256], [0, 256])
            hist_corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # รวมคะแนน (ปรับน้ำหนักใหม่)
            combined_score = (
                template_score * 0.3 +      # Template matching
                ssim_score * 0.3 +          # SSIM
                max(0, ncc_score) * 0.2 +   # NCC (เฉพาะค่าบวก)
                hist_corr * 0.2             # Histogram correlation
            )
            
            print(f"    Using combined score: template={template_score:.3f}, ssim={ssim_score:.3f}")
            
            return {
                'template': template_score,
                'ssim': ssim_score,
                'ncc': ncc_score,
                'histogram': hist_corr,
                'combined': combined_score
            }
            
        except Exception as e:
            print(f"❌ Similarity calculation error: {e}")
            return {
                'template': 0.0,
                'ssim': 0.0,
                'ncc': 0.0,
                'histogram': 0.0,
                'combined': 0.0
            }
    
    def get_template_info(self):
        """ดูข้อมูล templates ที่โหลดแล้ว"""
        return self.template_info
    
    def set_threshold(self, threshold):
        """ปรับค่า threshold"""
        self.threshold = threshold
        print(f"🔧 Threshold updated to: {threshold}")
    
    def test_detection(self, image_path):
        """ทดสอบการตรวจจับและแสดงผลละเอียด"""
        print(f"🧪 Testing detection on: {image_path}")
        
        result = self.detect_mission_pad(image_path)
        
        if result:
            print(f"✅ Result: Mission Pad ID {result['id']}")
            print(f"📊 Detailed scores:")
            for score_type, score_value in result['scores'].items():
                print(f"  {score_type}: {score_value:.3f}")
        else:
            print("❌ No mission pad detected")
        
        return result