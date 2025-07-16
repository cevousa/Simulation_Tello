#!/usr/bin/env python3
"""
Improved Mission Pad Detector - Enhanced version with multiple detection methods
ระบบตรวจจับ Mission Pad ที่ปรับปรุงใหม่ พร้อมวิธีการตรวจจับหลากหลาย
"""

import cv2
import numpy as np
import os
import json
from datetime import datetime

class ImprovedMissionPadDetector:
    def __init__(self, template_folder='mission_pad_templates'):
        """
        เริ่มต้น Mission Pad Detector ที่ปรับปรุงแล้ว
        
        Args:
            template_folder (str): โฟลเดอร์ที่เก็บ template images
        """
        self.template_folder = template_folder
        self.templates = {}
        self.detection_enabled = False
        self.confidence_threshold = 0.3
        self.detection_methods = ['template_matching', 'feature_matching', 'contour_detection']
        
        # โหลด templates
        self._load_templates()
        
    def _load_templates(self):
        """โหลดรูปภาพ template ทั้งหมดจากโฟลเดอร์"""
        try:
            print("🔧 Loading mission pad templates...")
            
            if not os.path.exists(self.template_folder):
                print(f"❌ Template folder not found: {self.template_folder}")
                return
            
            # ค้นหาโฟลเดอร์ใน template folder
            for item in os.listdir(self.template_folder):
                folder_path = os.path.join(self.template_folder, item)
                
                if os.path.isdir(folder_path):
                    # ดึงเลขจากชื่อโฟลเดอร์
                    try:
                        pad_id = int(item.split('_')[1])
                        
                        # ค้นหารูปภาพในโฟลเดอร์
                        for file in os.listdir(folder_path):
                            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                template_path = os.path.join(folder_path, file)
                                
                                # โหลดรูปภาพ
                                template_img = cv2.imread(template_path)
                                if template_img is not None:
                                    # เก็บทั้งแบบสีและขาวดำ
                                    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
                                    
                                    # สร้าง feature detector
                                    orb = cv2.ORB_create()
                                    kp, des = orb.detectAndCompute(template_gray, None)
                                    
                                    self.templates[pad_id] = {
                                        'image_color': template_img,
                                        'image_gray': template_gray,
                                        'path': template_path,
                                        'name': file,
                                        'keypoints': kp,
                                        'descriptors': des
                                    }
                                    print(f"  ✅ Loaded template {pad_id}: {file}")
                                break
                                
                    except (ValueError, IndexError):
                        print(f"  ⚠️ Cannot parse folder name: {item}")
                        continue
            
            print(f"✅ Loaded {len(self.templates)} mission pad templates")
            
        except Exception as e:
            print(f"❌ Failed to load templates: {e}")
            self.templates = {}
    
    def enable_mission_pad_detection(self):
        """เปิดใช้งาน Mission Pad detection"""
        self.detection_enabled = True
        print("✅ Mission Pad detection enabled")
    
    def disable_mission_pad_detection(self):
        """ปิดใช้งาน Mission Pad detection"""
        self.detection_enabled = False
        print("✅ Mission Pad detection disabled")
    
    def get_mission_pad_id(self, image_path=None):
        """
        ตรวจจับ Mission Pad ID จากรูปภาพ - ใช้วิธีการหลากหลาย
        
        Args:
            image_path (str): path ของรูปภาพที่ต้องการตรวจจับ
            
        Returns:
            int: Mission Pad ID ที่ตรวจพบ หรือ None ถ้าไม่พบ
        """
        if not self.detection_enabled:
            print("⚠️ Mission Pad detection is disabled")
            return None
        
        if not self.templates:
            print("❌ No templates loaded")
            return None
        
        if not image_path or not os.path.exists(image_path):
            print("❌ No valid image path provided")
            return None
        
        try:
            # อ่านรูปภาพที่ต้องการตรวจสอบ
            query_img = cv2.imread(image_path)
            if query_img is None:
                print(f"❌ Cannot load image: {image_path}")
                return None
            
            query_gray = cv2.cvtColor(query_img, cv2.COLOR_BGR2GRAY)
            
            print(f"🔍 Analyzing image: {image_path}")
            print(f"📏 Image size: {query_img.shape}")
            
            # ใช้วิธีการหลากหลายในการตรวจจับ
            results = {}
            
            # Method 1: Template Matching
            template_result = self._template_matching(query_gray)
            if template_result:
                results['template_matching'] = template_result
            
            # Method 2: Feature Matching
            feature_result = self._feature_matching(query_gray)
            if feature_result:
                results['feature_matching'] = feature_result
            
            # Method 3: Contour Detection
            contour_result = self._contour_detection(query_gray)
            if contour_result:
                results['contour_detection'] = contour_result
            
            # Method 4: Multi-scale Template Matching
            multiscale_result = self._multiscale_template_matching(query_gray)
            if multiscale_result:
                results['multiscale_template'] = multiscale_result
            
            # รวมผลลัพธ์จากทุกวิธี
            final_result = self._combine_results(results)
            
            if final_result:
                print(f"✅ Mission Pad detected: {final_result['id']} (confidence: {final_result['confidence']:.3f})")
                return final_result['id']
            else:
                print("❌ No mission pad detected with all methods")
                return None
                
        except Exception as e:
            print(f"❌ Mission Pad detection error: {e}")
            return None
    
    def _template_matching(self, query_gray):
        """วิธีการ Template Matching แบบปกติ"""
        try:
            best_match = None
            best_confidence = 0
            
            for pad_id, template_data in self.templates.items():
                template_gray = template_data['image_gray']
                
                # Template matching
                result = cv2.matchTemplate(query_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_match = pad_id
            
            if best_match and best_confidence >= self.confidence_threshold:
                print(f"  📋 Template Matching: {best_match} ({best_confidence:.3f})")
                return {'id': best_match, 'confidence': best_confidence, 'method': 'template_matching'}
            
            return None
            
        except Exception as e:
            print(f"❌ Template matching error: {e}")
            return None
    
    def _feature_matching(self, query_gray):
        """วิธีการ Feature Matching ด้วย ORB"""
        try:
            # สร้าง ORB detector
            orb = cv2.ORB_create()
            kp_query, des_query = orb.detectAndCompute(query_gray, None)
            
            if des_query is None:
                return None
            
            # สร้าง matcher
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            
            best_match = None
            best_score = 0
            
            for pad_id, template_data in self.templates.items():
                des_template = template_data['descriptors']
                
                if des_template is None:
                    continue
                
                # จับคู่ features
                matches = bf.match(des_query, des_template)
                
                if len(matches) > 0:
                    # เรียงลำดับตามระยะทาง
                    matches = sorted(matches, key=lambda x: x.distance)
                    
                    # คำนวณคะแนนจากจำนวนและคุณภาพของ matches
                    good_matches = [m for m in matches if m.distance < 50]
                    score = len(good_matches) / len(matches) if len(matches) > 0 else 0
                    
                    if score > best_score and len(good_matches) > 10:
                        best_score = score
                        best_match = pad_id
            
            if best_match and best_score > 0.3:
                print(f"  🔍 Feature Matching: {best_match} ({best_score:.3f})")
                return {'id': best_match, 'confidence': best_score, 'method': 'feature_matching'}
            
            return None
            
        except Exception as e:
            print(f"❌ Feature matching error: {e}")
            return None
    
    def _contour_detection(self, query_gray):
        """วิธีการ Contour Detection"""
        try:
            # หา contours
            edges = cv2.Canny(query_gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # หา contour ที่เป็นสี่เหลี่ยม
            for contour in contours:
                # ประมาณรูปร่าง
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # ตรวจสอบว่าเป็นสี่เหลี่ยมหรือไม่
                if len(approx) == 4:
                    area = cv2.contourArea(contour)
                    if area > 1000:  # กรองพื้นที่ที่เล็กเกินไป
                        # ในที่นี้อาจจะใช้วิธีอื่นเพื่อระบุเลข
                        print(f"  📐 Contour Detection: Found potential mission pad")
                        return {'id': 1, 'confidence': 0.5, 'method': 'contour_detection'}
            
            return None
            
        except Exception as e:
            print(f"❌ Contour detection error: {e}")
            return None
    
    def _multiscale_template_matching(self, query_gray):
        """วิธีการ Multi-scale Template Matching"""
        try:
            best_match = None
            best_confidence = 0
            
            scales = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
            
            for pad_id, template_data in self.templates.items():
                template_gray = template_data['image_gray']
                
                for scale in scales:
                    # ปรับขนาด template
                    width = int(template_gray.shape[1] * scale)
                    height = int(template_gray.shape[0] * scale)
                    
                    if width > query_gray.shape[1] or height > query_gray.shape[0]:
                        continue
                    
                    resized_template = cv2.resize(template_gray, (width, height))
                    
                    # Template matching
                    result = cv2.matchTemplate(query_gray, resized_template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)
                    
                    if max_val > best_confidence:
                        best_confidence = max_val
                        best_match = pad_id
            
            if best_match and best_confidence >= self.confidence_threshold:
                print(f"  📏 Multi-scale Template: {best_match} ({best_confidence:.3f})")
                return {'id': best_match, 'confidence': best_confidence, 'method': 'multiscale_template'}
            
            return None
            
        except Exception as e:
            print(f"❌ Multi-scale template matching error: {e}")
            return None
    
    def _combine_results(self, results):
        """รวมผลลัพธ์จากทุกวิธี"""
        if not results:
            return None
        
        # นับคะแนนสำหรับแต่ละ ID
        id_scores = {}
        
        for method, result in results.items():
            pad_id = result['id']
            confidence = result['confidence']
            
            if pad_id not in id_scores:
                id_scores[pad_id] = {'total_score': 0, 'count': 0, 'methods': []}
            
            id_scores[pad_id]['total_score'] += confidence
            id_scores[pad_id]['count'] += 1
            id_scores[pad_id]['methods'].append(method)
        
        # หาผลลัพธ์ที่ดีที่สุด
        best_id = None
        best_score = 0
        
        for pad_id, score_data in id_scores.items():
            # คำนวณคะแนนเฉลี่ย และให้น้ำหนักกับจำนวนวิธีที่ตรวจพบ
            avg_score = score_data['total_score'] / score_data['count']
            method_bonus = score_data['count'] * 0.1  # โบนัสสำหรับหลายวิธีที่ตรวจพบ
            final_score = avg_score + method_bonus
            
            if final_score > best_score:
                best_score = final_score
                best_id = pad_id
        
        if best_id:
            print(f"🎯 Combined result: ID {best_id} from {len(id_scores[best_id]['methods'])} methods")
            return {'id': best_id, 'confidence': best_score, 'method': 'combined'}
        
        return None
    
    def set_confidence_threshold(self, threshold):
        """กำหนดค่าเกณฑ์ความเชื่อมั่น"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        print(f"🔧 Confidence threshold set to: {self.confidence_threshold}")
    
    def get_template_info(self):
        """ดึงข้อมูลของ templates ที่โหลดไว้"""
        info = {}
        for pad_id, template_data in self.templates.items():
            info[pad_id] = {
                'name': template_data['name'],
                'path': template_data['path'],
                'size': template_data['image_gray'].shape,
                'has_features': template_data['descriptors'] is not None
            }
        return info
    
    def test_detection(self, test_image_path):
        """ทดสอบการตรวจจับด้วยรูปภาพทดสอบ"""
        print(f"🧪 Testing improved mission pad detection with: {test_image_path}")
        
        if not os.path.exists(test_image_path):
            print("❌ Test image not found")
            return None
        
        # เปิดการตรวจจับชั่วคราว
        was_enabled = self.detection_enabled
        self.enable_mission_pad_detection()
        
        # ทดสอบ
        result = self.get_mission_pad_id(test_image_path)
        
        # คืนค่าสถานะเดิม
        self.detection_enabled = was_enabled
        
        return result
    
    def debug_image_analysis(self, image_path):
        """วิเคราะห์รูปภาพแบบละเอียดเพื่อ debug"""
        if not os.path.exists(image_path):
            print("❌ Image not found")
            return
        
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            print(f"📊 Image Analysis for: {image_path}")
            print(f"📏 Size: {img.shape}")
            print(f"🔢 Pixel range: {gray.min()} - {gray.max()}")
            print(f"📈 Mean brightness: {gray.mean():.2f}")
            
            # แสดงข้อมูล templates
            print("\n🗂️ Available Templates:")
            for pad_id, template_data in self.templates.items():
                t_shape = template_data['image_gray'].shape
                print(f"  Template {pad_id}: {t_shape}")
            
            # ทดสอบการตรวจจับ
            print("\n🔍 Detection Test:")
            result = self.get_mission_pad_id(image_path)
            
            if result:
                print(f"✅ Final result: Mission Pad {result}")
            else:
                print("❌ No mission pad detected")
                
        except Exception as e:
            print(f"❌ Debug analysis error: {e}")
    
    def create_test_report(self, test_images_folder):
        """สร้างรายงานการทดสอบ"""
        if not os.path.exists(test_images_folder):
            print("❌ Test images folder not found")
            return
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'templates_loaded': len(self.templates),
            'confidence_threshold': self.confidence_threshold,
            'test_results': []
        }
        
        # ทดสอบกับรูปภาพทั้งหมดในโฟลเดอร์
        for file in os.listdir(test_images_folder):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(test_images_folder, file)
                
                print(f"🧪 Testing: {file}")
                result = self.test_detection(image_path)
                
                report['test_results'].append({
                    'image': file,
                    'detected_id': result,
                    'success': result is not None
                })
        
        # บันทึกรายงาน
        report_path = 'mission_pad_test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Test report saved to: {report_path}")
        
        # สรุปผล
        total_tests = len(report['test_results'])
        successful_tests = sum(1 for r in report['test_results'] if r['success'])
        
        print(f"📊 Test Summary: {successful_tests}/{total_tests} successful")
        
        return report
