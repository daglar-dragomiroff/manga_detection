import numpy as np
from ultralytics import YOLO
from PIL import Image
import cv2
from typing import List, Dict, Any

class BubbleDetector:
    def __init__(self, model_path: str, confidence: float = 0.5):
        """
        Инициализация детектора речевых пузырей
        
        Args:
            model_path: путь к файлу модели YOLOv8
            confidence: порог уверенности для детекции
        """
        self.model = YOLO(model_path)
        self.confidence = confidence
        
    def detect_bubbles(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Обнаружение речевых пузырей на изображении
        
        Args:
            image_path: путь к изображению
            
        Returns:
            Список словарей с информацией о найденных пузырях
        """
        results = self.model(image_path, conf=self.confidence)
        
        bubbles = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    # Извлекаем координаты и метаданные
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    bubbles.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(confidence),
                        'class_id': class_id
                    })
        
        return bubbles
    
    def visualize_detection(self, image_path: str, bubbles: List[Dict]) -> np.ndarray:
        """
        Создание визуализации с найденными пузырями
        
        Args:
            image_path: путь к исходному изображению
            bubbles: список найденных пузырей
            
        Returns:
            Изображение с нарисованными bounding box'ами
        """
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        for i, bubble in enumerate(bubbles):
            x1, y1, x2, y2 = bubble['bbox']
            confidence = bubble['confidence']
            
            # Рисуем прямоугольник
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Добавляем номер пузыря
            label = f"#{i+1} ({confidence:.2f})"
            cv2.putText(image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        return image