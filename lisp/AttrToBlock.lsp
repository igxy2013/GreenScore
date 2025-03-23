(defun c:AttrToBlock (/ ss i ent entData attTag pt blkName blkDef)
  (vl-load-com) ; 启用 ActiveX 函数
  (setvar "CMDECHO" 0) ; 关闭命令回显
  (princ "\n程序已启动...")
  
  ;; 选择所有属性定义
  (setq ss (ssget "_X" '((0 . "ATTDEF"))))
  
  (if (not ss)
    (progn
      (princ "\n未找到属性定义，请手动选择属性定义...")
      (setq ss (ssget '((0 . "ATTDEF"))))
    )
  )
  
  (if ss
    (progn
      (princ (strcat "\n找到 " (itoa (sslength ss)) " 个属性定义。"))
      
      ;; 遍历每个属性定义
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq entData (entget ent))
        
        ;; 获取属性定义的标记和位置
        (setq attTag (cdr (assoc 2 entData))) ; 标记
        (setq pt (cdr (assoc 10 entData)))    ; 基点
        
        ;; 自动生成唯一块名称（避免浮点数错误）
        (setq blkName (strcat "AutoBlock_"
                              (substr (rtos (getvar "CDATE") 2 6) 1 8) ; 提取日期整数部分（如20240716）
                              "_"
                              (itoa i)
                        )
        )
        
        ;; 通过 ActiveX 创建块定义（完全无交互）
        (setq blkDef (vla-add (vla-get-blocks (vla-get-activedocument (vlax-get-acad-object))) 
                              (vlax-3d-point pt) 
                              blkName
                        )
        )
        
        ;; 将属性定义复制到块中
        (vla-copyobjects (vla-get-activedocument (vlax-get-acad-object)) 
                         (vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbObject '(0 . 0)) 
                                           (list (vlax-ename->vla-object ent))
                                  )
                         )
                         blkDef
        )
        
        ;; 插入块（无交互）
        (vla-insertblock 
          (vla-get-modelspace (vla-get-activedocument (vlax-get-acad-object))) 
          (vlax-3d-point pt) 
          blkName 
          1.0 1.0 1.0 0.0 ; X/Y/Z 比例因子为1，旋转角度0
        )
        
        ;; 删除原始属性定义
        (entdel ent)
        
        (setq i (1+ i))
      )
      (princ (strcat "\n已将 " (itoa (sslength ss)) " 个属性定义转换为块。"))
    )
    (princ "\n未找到属性定义。")
  )
  (setvar "CMDECHO" 1)
  (princ "\n程序已结束...")
  (princ)
)