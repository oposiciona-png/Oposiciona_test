import fitz  # PyMuPDF
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import sys
import os
import random
import webbrowser  # Necesario para abrir el enlace web

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, compatible con PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PDFQuizParser:
    @staticmethod
    def parse(pdf_path):
        doc = fitz.open(pdf_path)
        questions = []
        
        lines = []
        stop_reading = False # El interruptor general irrevocable del PDF
        
        for page in doc:
            if stop_reading:
                break
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if stop_reading:
                    break
                if b.get("type", 0) == 0:  
                    for l in b["lines"]:
                        line_text = ""
                        is_bold = False
                        for s in l["spans"]:
                            text = s["text"].strip()
                            if not text:
                                continue
                            line_text += text + " "
                            if "bold" in s["font"].lower() or (s["flags"] & 2 != 0):
                                is_bold = True
                        
                        line_text = line_text.strip()
                        if line_text:
                            tl = line_text.lower()
                            tl_nospace = tl.replace(" ", "").replace(".", "").replace("-", "").replace(":", "")
                            
                            # --- FRENO DE EMERGENCIA DE HIERRO (Actúa ANTES de filtrar nada) ---
                            if ("preguntadedesarrollo" in tl_nospace or 
                                "preguntasdedesarrollo" in tl_nospace or 
                                "supuestopractico" in tl_nospace or 
                                "supuestopráctico" in tl_nospace or 
                                "plantilladerespuesta" in tl_nospace or 
                                "plantillasderespuesta" in tl_nospace):
                                stop_reading = True
                                break
                            
                            # --- FILTRO UNIVERSAL DE CABECERAS Y PIES DE PÁGINA ---
                            is_header = False
                            if len(tl) < 80:
                                if "www.oposiciona.es" in tl or re.search(r'^p[áa]gina\s+\d+\s+de\s+\d+', tl) or tl == "oposiciona":
                                    is_header = True
                                elif "administrativo de la seguridad social" in tl or "gestion de la seguridad social" in tl or "gestión de la seguridad social" in tl:
                                    is_header = True
                                elif "examen repaso" in tl or "test tema" in tl or "respuestas test" in tl or re.search(r'^tema\s+\d+', tl) or re.search(r'^examen\s+', tl) or "normas para la realización" in tl:
                                    is_header = True
                            
                            if is_header:
                                continue
                                
                            lines.append({"text": line_text, "bold": is_bold})
                            
        current_q = None
        preamble = "" 
        expected_q_num = 1  
        
        for line in lines:
            text = line["text"]
            is_bold = line["bold"]
            text_lower = text.lower()
            
            is_option = bool(re.match(r'^[a-zA-Z][\)\.]\s', text))
            is_explanation = text_lower.startswith("explicaci") or text_lower.startswith("resp:") or text_lower.startswith("respuesta:")
            
            # Las "Preguntas de Reserva" se incluyen y no cortan el examen
            if re.match(r'^\s*(preguntas?\s+de\s+reserva)', text_lower):
                if current_q and current_q["options"]:
                    questions.append(current_q)
                current_q = None 
                preamble += text + "\n"
                continue

            # --- DETECTOR DE PREGUNTAS BLINDADO ---
            is_new_q = False
            m_num = re.match(r'^\s*(\d+)[\.-]+(?!\d)', text) or re.match(r'^\s*(\d+)\s+[\.-]', text)
            m_rescue = False
            
            # Escáner de rescate
            if not m_num and not is_option and not is_explanation:
                text_clean = text.strip()
                if (current_q and current_q["state"] in ["E", "O"]) or not current_q:
                    if re.match(r'^\s*\d+¿', text_clean) or (
                       re.match(r'^\s*(¿|C[óo]mo|Cu[áa]l|Cu[áa]ntos|Qu[ée])\b', text_clean, re.IGNORECASE) and text_clean.endswith('?')
                    ):
                        m_rescue = True

            # Candado Matemático flexible (tolera saltos a preguntas de reserva)
            if m_num:
                num = int(m_num.group(1))
                if current_q is None:
                    is_new_q = True
                    expected_q_num = num + 1
                elif expected_q_num - 20 <= num <= expected_q_num + 50:
                    is_new_q = True
                    expected_q_num = num + 1
            elif m_rescue:
                is_new_q = True
                expected_q_num += 1

            if is_new_q:
                if current_q and current_q["options"]:
                    questions.append(current_q)
                
                clean_text = re.sub(r'^\s*\d+[\.-]+\s*(-*\s*)?', '', text)
                clean_text = re.sub(r'^\s*\d+¿', '¿', clean_text)
                
                current_q = {
                    "preamble": preamble.strip(),
                    "question_text": clean_text,
                    "options": [],
                    "answer": -1,
                    "explanation": "",
                    "state": "Q"
                }
                preamble = "" 
                continue
                
            if not current_q:
                preamble += text + "\n"
                continue
                
            if is_option and current_q["state"] in ["Q", "O"]:
                current_q["options"].append(text)
                current_q["state"] = "O"
                if is_bold and current_q["answer"] == -1:
                    current_q["answer"] = len(current_q["options"]) - 1
                continue
                
            if is_explanation:
                if current_q:
                    current_q["explanation"] += text + " "
                    current_q["state"] = "E"
                continue
                
            if current_q["state"] == "Q":
                current_q["question_text"] += " " + text
            elif current_q["state"] == "O":
                last_opt = current_q["options"][-1].strip()
                
                is_new_paragraph = len(current_q["options"]) >= 2 and re.search(r'[\.;]$', last_opt) and re.match(r'^[A-Z0-9¿¡"\'«]', text)
                is_legal_ref = re.match(r'^(art[íi]culo|ley|real decreto|orden|disposici[óo]n|según|normativa)', text_lower)
                
                if is_new_paragraph or is_legal_ref:
                    current_q["state"] = "E"
                    current_q["explanation"] = text
                else:
                    if is_bold and current_q["answer"] == -1:
                        current_q["answer"] = len(current_q["options"]) - 1
                    current_q["options"][-1] += " " + text
            elif current_q["state"] == "E":
                current_q["explanation"] += " " + text

        if current_q and current_q["options"]:
            questions.append(current_q)
            
        return questions

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Practicador de Tests PDF")
        
        try:
            self.root.state('zoomed')
        except:
            self.root.attributes('-fullscreen', True)
            
        self.questions = []
        self.current_q_index = 0
        self.q_stats = {} 
        self.table_frame = None 
        
        self.canvas = tk.Canvas(root, bg="#f9f9f9", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#f9f9f9")
        
        self.frame_id = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)

        try:
            # Empaquetamos el logo
            self.logo_img = tk.PhotoImage(file=resource_path("oposiciona (320 x 132 px).png"))
            self.logo_label = tk.Label(self.scroll_frame, image=self.logo_img, bg="#f9f9f9")
            self.logo_label.pack(pady=(20, 5))
            
            # Enlace clickeable justo debajo del logo
            self.link_label = tk.Label(self.scroll_frame, text="www.oposiciona.es", font=("Arial", 16, "underline"), fg="blue", bg="#f9f9f9", cursor="hand2")
            self.link_label.pack(pady=(0, 20))
            self.link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://oposiciona.es/"))
            
        except Exception as e:
            print("No se pudo cargar el logo o el enlace:", e)
        
        self.load_btn = tk.Button(self.scroll_frame, text="Cargar PDF de Test", command=self.load_pdf, font=("Arial", 18, "bold"), bg="#4CAF50", fg="white", padx=20, pady=10)
        self.load_btn.pack(pady=20)
        
        self.q_label = tk.Label(self.scroll_frame, text="Sube un PDF para comenzar...", font=("Arial", 20, "bold"), bg="#f9f9f9", justify="left", anchor="w")
        self.q_label.pack(fill="x", pady=20, padx=40)
        
        self.var = tk.IntVar()
        self.var.set(-1)
        self.option_buttons = []
        for i in range(6): 
            rb = tk.Radiobutton(self.scroll_frame, text="", variable=self.var, value=i, font=("Arial", 18), bg="#f9f9f9", justify="left", anchor="w", cursor="hand2")
            self.option_buttons.append(rb)
            
        self.main_btn_frame = tk.Frame(self.scroll_frame, bg="#f9f9f9")
        
        self.prev_btn = tk.Button(self.main_btn_frame, text="🡄 Pregunta Anterior", command=self.prev_question, font=("Arial", 16, "bold"), bg="#e0e0e0", padx=15, pady=8, cursor="hand2")
        self.check_btn = tk.Button(self.main_btn_frame, text="Comprobar Respuesta", command=self.check_answer, font=("Arial", 16, "bold"), bg="lightblue", padx=15, pady=8, cursor="hand2")
        self.skip_btn = tk.Button(self.main_btn_frame, text="Siguiente Pregunta ➔", command=self.next_question, font=("Arial", 16, "bold"), bg="#e0e0e0", padx=15, pady=8, cursor="hand2")
        self.end_test_btn = tk.Button(self.main_btn_frame, text="⏹ Finalizar Test", command=self.end_test_early, font=("Arial", 16, "bold"), bg="#ff9800", fg="white", padx=15, pady=8, cursor="hand2")
        
        self.results_label = tk.Label(self.scroll_frame, text="", font=("Arial", 18), bg="#f9f9f9", justify="left")
        
        self.results_btn_frame = tk.Frame(self.scroll_frame, bg="#f9f9f9")
        self.restart_btn = tk.Button(self.results_btn_frame, text="🔄 Repetir este Test", command=self.restart_test, font=("Arial", 16, "bold"), bg="#4CAF50", fg="white", padx=15, pady=8, cursor="hand2")
        self.new_file_btn = tk.Button(self.results_btn_frame, text="📁 Cargar otro PDF", command=self.load_new_pdf, font=("Arial", 16, "bold"), bg="#2196F3", fg="white", padx=15, pady=8, cursor="hand2")
        self.exit_btn = tk.Button(self.results_btn_frame, text="❌ Finalizar", command=self.root.quit, font=("Arial", 16, "bold"), bg="#f44336", fg="white", padx=15, pady=8, cursor="hand2")
        
        self.restart_btn.pack(side="left", padx=10)
        self.new_file_btn.pack(side="left", padx=10)
        self.exit_btn.pack(side="left", padx=10)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.frame_id, width=event.width)
        wrap_width = event.width - 150
        if wrap_width > 0:
            self.q_label.config(wraplength=wrap_width)
            for rb in self.option_buttons:
                rb.config(wraplength=wrap_width)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            try:
                parsed_questions = PDFQuizParser.parse(filepath)
                if not parsed_questions:
                    messagebox.showwarning("Aviso", "No se encontraron preguntas válidas en este PDF.")
                    return
                
                for q in parsed_questions:
                    if q["options"]:
                        cleaned_options = []
                        for opt in q["options"]:
                            cleaned = re.sub(r'^[a-zA-Z][\)\.-]\s*', '', opt).strip()
                            cleaned_options.append(cleaned)
                        q["options"] = cleaned_options
                        
                        correct_opt_text = None
                        if q["answer"] != -1 and q["answer"] < len(q["options"]):
                            correct_opt_text = q["options"][q["answer"]]
                            
                        random.shuffle(q["options"])
                        
                        if correct_opt_text is not None:
                            q["answer"] = q["options"].index(correct_opt_text)
                            
                        for i in range(len(q["options"])):
                            letter = chr(97 + i)
                            q["options"][i] = f"{letter}) {q['options'][i]}"
                            
                random.shuffle(parsed_questions)
                self.questions = parsed_questions
                
                self.restart_test()
                self.load_btn.pack_forget() 
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def load_new_pdf(self):
        self.results_label.pack_forget()
        self.results_btn_frame.pack_forget()
        if self.table_frame:
            self.table_frame.destroy()
            self.table_frame = None
            
        self.load_pdf()

    def restart_test(self):
        self.q_stats = {i: {'attempts': 0, 'status': 'blank', 'selected_option': -1} for i in range(len(self.questions))}
        self.current_q_index = 0
        
        self.results_label.pack_forget()
        self.results_btn_frame.pack_forget()
        if self.table_frame:
            self.table_frame.destroy()
            self.table_frame = None
            
        self.show_question()

    def save_current_state(self):
        """Guarda la respuesta actual y suma intento SOLAMENTE si la opción ha cambiado."""
        if self.current_q_index < len(self.questions):
            selected = self.var.get()
            correct = self.questions[self.current_q_index]["answer"]
            prev_selected = self.q_stats[self.current_q_index]['selected_option']
            
            if selected != -1 and selected != prev_selected:
                self.q_stats[self.current_q_index]['attempts'] += 1
                self.q_stats[self.current_q_index]['selected_option'] = selected
                if selected == correct:
                    self.q_stats[self.current_q_index]['status'] = 'correct'
                else:
                    self.q_stats[self.current_q_index]['status'] = 'incorrect'
            elif selected == -1 and self.q_stats[self.current_q_index]['attempts'] == 0:
                self.q_stats[self.current_q_index]['status'] = 'blank'

    def end_test_early(self):
        if messagebox.askyesno("Finalizar Test", "¿Estás seguro de que quieres finalizar el test anticipadamente?\n\nLas preguntas restantes se contarán como en blanco."):
            self.save_current_state()
            self.current_q_index = len(self.questions) 
            self.show_results()

    def show_question(self):
        self.canvas.yview_moveto(0)
        
        if self.current_q_index < len(self.questions):
            q_data = self.questions[self.current_q_index]
            
            q_text = ""
            if q_data["preamble"]:
                q_text += q_data["preamble"] + "\n\n"
            q_text += f"{self.current_q_index + 1}.- {q_data['question_text']}"
            
            self.q_label.config(text=f"Pregunta {self.current_q_index + 1} de {len(self.questions)}\n\n{q_text}")
            
            prev_selected = self.q_stats[self.current_q_index]['selected_option']
            self.var.set(prev_selected)
            
            self.main_btn_frame.pack_forget()
            
            for rb in self.option_buttons:
                rb.pack_forget()
                
            for i, opt in enumerate(q_data["options"]):
                if i < len(self.option_buttons):
                    self.option_buttons[i].config(text=opt, value=i)
                    self.option_buttons[i].pack(fill="x", padx=40, pady=10)
            
            self.main_btn_frame.pack(pady=30, padx=40, anchor="w")
            
            for widget in self.main_btn_frame.winfo_children():
                widget.pack_forget()
                
            if self.current_q_index > 0:
                self.prev_btn.pack(side="left", padx=10)
                
            self.check_btn.pack(side="left", padx=10)
            
            if self.current_q_index < len(self.questions) - 1:
                self.skip_btn.config(text="Siguiente Pregunta ➔", bg="#e0e0e0", fg="black")
                self.skip_btn.pack(side="left", padx=10)
                self.end_test_btn.pack(side="left", padx=10) 
            else:
                self.skip_btn.config(text="Terminar y ver resultados ➔", bg="#FF9800", fg="white")
                self.skip_btn.pack(side="left", padx=10)
                
        else:
            self.show_results()

    def show_results(self):
        self.canvas.yview_moveto(0)
        
        self.q_label.config(text="¡Has finalizado el test!")
        for rb in self.option_buttons:
            rb.pack_forget()
            
        self.main_btn_frame.pack_forget() 
        
        aciertos = sum(1 for v in self.q_stats.values() if v['status'] == 'correct')
        fallos = sum(1 for v in self.q_stats.values() if v['status'] == 'incorrect')
        blancos = sum(1 for v in self.q_stats.values() if v['status'] == 'blank')
        
        total = len(self.questions)
        nota = (aciertos / total) * 10 if total > 0 else 0
        
        res_text = "📊 RESULTADOS FINALES DEL TEST\n"
        res_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        res_text += f"✅ Acertadas:  {aciertos}\n"
        res_text += f"❌ Falladas:   {fallos}\n"
        res_text += f"⚪ En blanco:  {blancos}\n\n"
        res_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        res_text += f"🎓 NOTA FINAL:  {nota:.2f} / 10\n"
        res_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                
        self.results_label.config(text=res_text)
        self.results_label.pack(pady=10, padx=60, anchor="w")
        
        self.table_frame = tk.Frame(self.scroll_frame, bg="#f9f9f9")
        self.table_frame.pack(pady=10, padx=60, fill="x", expand=True)
        
        text_widget = tk.Text(self.table_frame, wrap="word", height=25, bg="#ffffff", padx=20, pady=20, relief="flat", highlightbackground="#cccccc", highlightthickness=1)
        text_scroll = tk.Scrollbar(self.table_frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=text_scroll.set)
        
        text_scroll.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)
        
        # FUENTE AMPLIADA: 16 para el cuerpo, 18 para las cabeceras (100% comodidad visual)
        text_widget.tag_configure("header", font=("Arial", 18, "bold"), foreground="#333333")
        text_widget.tag_configure("correct", font=("Arial", 18, "bold"), foreground="green")
        text_widget.tag_configure("incorrect", font=("Arial", 18, "bold"), foreground="red")
        text_widget.tag_configure("blank", font=("Arial", 18, "bold"), foreground="#FF8C00")
        
        text_widget.tag_configure("bold_body", font=("Arial", 16, "bold"), foreground="#000000")
        text_widget.tag_configure("body", font=("Arial", 16), foreground="#000000")
        
        for i in range(total):
            stat = self.q_stats.get(i, {'attempts': 0, 'status': 'blank'})
            q_data = self.questions[i]
            
            if stat['status'] == 'correct':
                res_str = "✅ Correcta"
                res_tag = "correct"
            elif stat['status'] == 'incorrect':
                res_str = "❌ Incorrecta"
                res_tag = "incorrect"
            else:
                res_str = "⚪ En blanco"
                res_tag = "blank"
                
            intentos = stat['attempts'] if stat['attempts'] > 0 else "-"
            
            text_widget.insert(tk.END, f"Pregunta {i+1} | ", "header")
            text_widget.insert(tk.END, f"{res_str}", res_tag)
            text_widget.insert(tk.END, f" | Intentos: {intentos}\n\n", "header")
            
            text_widget.insert(tk.END, "Pregunta: ", "bold_body")
            text_widget.insert(tk.END, f"{q_data.get('question_text', '')}\n\n", "body")
            
            correct_opt = "?"
            if q_data["answer"] != -1 and q_data["answer"] < len(q_data["options"]):
                correct_opt = q_data["options"][q_data["answer"]]
            
            text_widget.insert(tk.END, "Respuesta correcta: ", "bold_body")
            text_widget.insert(tk.END, f"{correct_opt}\n\n", "body")
            
            exp_text = q_data.get('explanation', '').strip()
            if not exp_text:
                exp_text = "No hay explicación disponible para esta pregunta."
            
            text_widget.insert(tk.END, "Explicación: ", "bold_body")
            text_widget.insert(tk.END, f"{exp_text}\n\n", "body")
            
            text_widget.insert(tk.END, "━" * 80 + "\n\n", "body")
            
        text_widget.config(state=tk.DISABLED) 
        
        self.results_btn_frame.pack(pady=30, padx=60, anchor="center")

    def check_answer(self):
        self.save_current_state()
        
        selected = self.var.get()
        q_data = self.questions[self.current_q_index]
        correct = q_data["answer"]
        
        popup = tk.Toplevel(self.root)
        popup.title("Resultado de la pregunta")
        popup.geometry("900x700")
        popup.configure(bg="#ffffff")
        
        popup.transient(self.root)
        popup.grab_set()
        
        btn_frame = tk.Frame(popup, bg="#ffffff")
        btn_frame.pack(side=tk.BOTTOM, pady=20, fill="x")
        
        center_btn_frame = tk.Frame(btn_frame, bg="#ffffff")
        center_btn_frame.pack(expand=True)
        
        def on_repeat():
            popup.destroy()
            self.var.set(-1) 
            self.q_stats[self.current_q_index]['selected_option'] = -1 

        def on_next():
            popup.destroy()
            self.current_q_index += 1
            self.show_question()
            
        btn_repeat = tk.Button(center_btn_frame, text="Repetir Pregunta", command=on_repeat, font=("Arial", 16), bg="#e0e0e0", cursor="hand2", padx=20, pady=10)
        btn_repeat.pack(side="left", padx=20)
        
        texto_siguiente = "Terminar y ver resultados ➔" if self.current_q_index == len(self.questions) - 1 else "Siguiente Pregunta ➔"
        btn_next = tk.Button(center_btn_frame, text=texto_siguiente, command=on_next, font=("Arial", 16, "bold"), bg="#FFC107", cursor="hand2", padx=20, pady=10)
        btn_next.pack(side="left", padx=20)

        lbl_title = tk.Label(popup, font=("Arial", 22, "bold"), bg="#ffffff")
        lbl_title.pack(side=tk.TOP, pady=20)
        
        correct_letter = "?"
        if correct != -1:
            correct_text = q_data["options"][correct]
            m = re.match(r'^([a-eA-E])[\)\.]', correct_text.strip())
            if m:
                correct_letter = m.group(1).upper()
            else:
                correct_letter = chr(97 + correct).upper()
        
        if selected == -1:
            lbl_title.config(text=f"⚪ PREGUNTA EN BLANCO. La respuesta era la {correct_letter}.", fg="#FF8C00")
        elif selected == correct:
            lbl_title.config(text="✅ ¡CORRECTO!", fg="green")
        else:
            lbl_title.config(text=f"❌ INCORRECTO. La respuesta correcta era la {correct_letter}.", fg="red")
            
        exp_text = q_data.get('explanation', '')
        
        exp_frame = tk.Frame(popup, bg="#ffffff")
        exp_frame.pack(side=tk.TOP, padx=30, pady=10, fill="both", expand=True)
        
        exp_scroll = tk.Scrollbar(exp_frame)
        exp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(exp_frame, font=("Arial", 18), wrap="word", bg="#f4f4f4", relief="flat", padx=20, pady=20, yscrollcommand=exp_scroll.set)
        text_widget.pack(side=tk.LEFT, fill="both", expand=True)
        
        exp_scroll.config(command=text_widget.yview)
        
        if exp_text:
            text_widget.insert(tk.END, f"{exp_text}")
        else:
            text_widget.insert(tk.END, "No hay explicación disponible para esta pregunta.")
            
        text_widget.config(state=tk.DISABLED)

    def next_question(self):
        self.save_current_state()
        self.current_q_index += 1
        self.show_question()

    def prev_question(self):
        self.save_current_state()
        self.current_q_index -= 1
        self.show_question()

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()