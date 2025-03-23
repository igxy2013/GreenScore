(defun c:AttrToBlock (/ ss i ent entData attTag pt blkName blkDef)
  (vl-load-com) ; ���� ActiveX ����
  (setvar "CMDECHO" 0) ; �ر��������
  (princ "\n����������...")
  
  ;; ѡ���������Զ���
  (setq ss (ssget "_X" '((0 . "ATTDEF"))))
  
  (if (not ss)
    (progn
      (princ "\nδ�ҵ����Զ��壬���ֶ�ѡ�����Զ���...")
      (setq ss (ssget '((0 . "ATTDEF"))))
    )
  )
  
  (if ss
    (progn
      (princ (strcat "\n�ҵ� " (itoa (sslength ss)) " �����Զ��塣"))
      
      ;; ����ÿ�����Զ���
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq entData (entget ent))
        
        ;; ��ȡ���Զ���ı�Ǻ�λ��
        (setq attTag (cdr (assoc 2 entData))) ; ���
        (setq pt (cdr (assoc 10 entData)))    ; ����
        
        ;; �Զ�����Ψһ�����ƣ����⸡��������
        (setq blkName (strcat "AutoBlock_"
                              (substr (rtos (getvar "CDATE") 2 6) 1 8) ; ��ȡ�����������֣���20240716��
                              "_"
                              (itoa i)
                        )
        )
        
        ;; ͨ�� ActiveX �����鶨�壨��ȫ�޽�����
        (setq blkDef (vla-add (vla-get-blocks (vla-get-activedocument (vlax-get-acad-object))) 
                              (vlax-3d-point pt) 
                              blkName
                        )
        )
        
        ;; �����Զ��帴�Ƶ�����
        (vla-copyobjects (vla-get-activedocument (vlax-get-acad-object)) 
                         (vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbObject '(0 . 0)) 
                                           (list (vlax-ename->vla-object ent))
                                  )
                         )
                         blkDef
        )
        
        ;; ����飨�޽�����
        (vla-insertblock 
          (vla-get-modelspace (vla-get-activedocument (vlax-get-acad-object))) 
          (vlax-3d-point pt) 
          blkName 
          1.0 1.0 1.0 0.0 ; X/Y/Z ��������Ϊ1����ת�Ƕ�0
        )
        
        ;; ɾ��ԭʼ���Զ���
        (entdel ent)
        
        (setq i (1+ i))
      )
      (princ (strcat "\n�ѽ� " (itoa (sslength ss)) " �����Զ���ת��Ϊ�顣"))
    )
    (princ "\nδ�ҵ����Զ��塣")
  )
  (setvar "CMDECHO" 1)
  (princ "\n�����ѽ���...")
  (princ)
)