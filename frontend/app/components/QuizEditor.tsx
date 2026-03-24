"use client";

import React, { useState } from "react";

interface QuizEditorProps {
    courseData: any;
    hasActiveRequest: boolean;
    saveCourseData: (updatedCourse: any) => Promise<void>;
    setUiNotice: (notice: { type: "success" | "error"; text: string } | null) => void;
}

export function QuizEditor({
    courseData,
    hasActiveRequest,
    saveCourseData,
    setUiNotice,
}: QuizEditorProps) {
    const [editingQuiz, setEditingQuiz] = useState(false);
    const [quizCache, setQuizCache] = useState<any>({});
    const [quizBusy, setQuizBusy] = useState(false);

    const toggleEditQuiz = () => {
        const isEditing = !editingQuiz;
        setEditingQuiz(isEditing);
        if (isEditing) {
            setQuizCache(JSON.parse(JSON.stringify(courseData.quiz || {})));
        }
    };

    const saveQuiz = async () => {
        if (!quizCache) return;
        if (quizBusy) return;
        setQuizBusy(true);
        setUiNotice(null);

        try {
            const updated = { ...courseData };
            updated.quiz = {
                ...updated.quiz,
                quizTitle: quizCache.quizTitle,
                questions: quizCache.questions || [],
            };
            await saveCourseData(updated);
            setEditingQuiz(false);
            setUiNotice({ type: "success", text: "Final Quiz changes saved." });
        } catch (err: any) {
            setUiNotice({ type: "error", text: `Failed to save quiz: ${err?.message || "Unknown error"}` });
        } finally {
            setQuizBusy(false);
        }
    };

    if (!courseData || !courseData.quiz) return null;

    return (
        <div className="card surface">
            <div className="inline" style={{ justifyContent: "space-between", width: "100%" }}>
                <h2 className="section-title">Final Quiz</h2>
                <div className="inline" style={{ gap: 8 }}>
                    <button type="button" className="secondary" disabled={hasActiveRequest} onClick={toggleEditQuiz} style={{ fontSize: "0.82rem", padding: "6px 12px" }}>
                        {editingQuiz ? "Cancel" : "Edit"}
                    </button>
                    {editingQuiz && <span style={{ fontSize: "0.82rem", background: "rgba(27,90,166,0.1)", color: "var(--accent)", padding: "4px 10px", borderRadius: "100px", fontWeight: 600 }}>💡 Press Enter to save</span>}
                </div>
            </div>

            {editingQuiz ? (
                <div style={{ marginTop: "16px" }}>
                    <div className="field">
                        <label>Quiz Title</label>
                        <input
                            value={quizCache.quizTitle || ""}
                            onChange={(e) => setQuizCache({ ...quizCache, quizTitle: e.target.value })}
                            onKeyDown={(e) => { if (e.key === 'Enter') void saveQuiz(); }}
                        />
                    </div>

                    <h3 style={{ marginTop: "24px", marginBottom: "16px" }}>Questions</h3>
                    {(quizCache.questions || []).map((q: any, qIndex: number) => (
                        <div key={qIndex} style={{ border: "1px solid var(--border)", padding: "16px", borderRadius: "8px", marginBottom: "16px" }}>
                            <div className="inline" style={{ justifyContent: "space-between", marginBottom: "12px" }}>
                                <label style={{ fontSize: "1.05rem", fontWeight: 600 }}>Question {qIndex + 1}</label>
                                <button
                                    type="button"
                                    className="secondary"
                                    disabled={hasActiveRequest}
                                    onClick={() => {
                                        const newQ = [...(quizCache.questions || [])];
                                        newQ.splice(qIndex, 1);
                                        setQuizCache({ ...quizCache, questions: newQ });
                                    }}
                                >
                                    Remove
                                </button>
                            </div>

                            <div className="field" style={{ marginBottom: "16px" }}>
                                <input
                                    value={q.question || ""}
                                    placeholder="Enter question text..."
                                    onChange={(e) => {
                                        const newQ = [...(quizCache.questions || [])];
                                        newQ[qIndex] = { ...newQ[qIndex], question: e.target.value };
                                        setQuizCache({ ...quizCache, questions: newQ });
                                    }}
                                    onKeyDown={(e) => { if (e.key === 'Enter') void saveQuiz(); }}
                                />
                            </div>

                            <div className="responsive-two-col" style={{ marginBottom: "16px" }}>
                                {['A', 'B', 'C', 'D'].map((opt) => (
                                    <div className="field" key={opt} style={{ margin: 0 }}>
                                        <label>Option {opt}</label>
                                        <input
                                            value={q.options?.[opt] || ""}
                                            onChange={(e) => {
                                                const newQ = [...(quizCache.questions || [])];
                                                newQ[qIndex] = {
                                                    ...newQ[qIndex],
                                                    options: { ...newQ[qIndex]?.options, [opt]: e.target.value }
                                                };
                                                setQuizCache({ ...quizCache, questions: newQ });
                                            }}
                                            onKeyDown={(e) => { if (e.key === 'Enter') void saveQuiz(); }}
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="field" style={{ marginBottom: "16px" }}>
                                <label>Correct Answer</label>
                                <select
                                    value={q.correctAnswer || "A"}
                                    onChange={(e) => {
                                        const newQ = [...(quizCache.questions || [])];
                                        newQ[qIndex] = { ...newQ[qIndex], correctAnswer: e.target.value };
                                        setQuizCache({ ...quizCache, questions: newQ });
                                    }}
                                    style={{ padding: "8px", borderRadius: "4px", border: "1px solid var(--border)", background: "var(--background)", color: "var(--foreground)", width: "100%", maxWidth: "200px", display: "block" }}
                                >
                                    <option value="A">Option A</option>
                                    <option value="B">Option B</option>
                                    <option value="C">Option C</option>
                                    <option value="D">Option D</option>
                                </select>
                            </div>

                            <div className="responsive-two-col">
                                <div className="field" style={{ margin: 0 }}>
                                    <label>Feedback (If Correct)</label>
                                    <input
                                        value={q.feedback?.correct || ""}
                                        onChange={(e) => {
                                            const newQ = [...(quizCache.questions || [])];
                                            newQ[qIndex] = {
                                                ...newQ[qIndex],
                                                feedback: { ...newQ[qIndex]?.feedback, correct: e.target.value }
                                            };
                                            setQuizCache({ ...quizCache, questions: newQ });
                                        }}
                                        onKeyDown={(e) => { if (e.key === 'Enter') void saveQuiz(); }}
                                    />
                                </div>
                                <div className="field" style={{ margin: 0 }}>
                                    <label>Feedback (If Incorrect)</label>
                                    <input
                                        value={q.feedback?.incorrect || ""}
                                        onChange={(e) => {
                                            const newQ = [...(quizCache.questions || [])];
                                            newQ[qIndex] = {
                                                ...newQ[qIndex],
                                                feedback: { ...newQ[qIndex]?.feedback, incorrect: e.target.value }
                                            };
                                            setQuizCache({ ...quizCache, questions: newQ });
                                        }}
                                        onKeyDown={(e) => { if (e.key === 'Enter') void saveQuiz(); }}
                                    />
                                </div>
                            </div>
                        </div>
                    ))}

                    <button
                        type="button"
                        className="secondary"
                        disabled={hasActiveRequest}
                        onClick={() => {
                            const newQ = [...(quizCache.questions || [])];
                            newQ.push({
                                questionNumber: newQ.length + 1,
                                question: "",
                                options: { A: "", B: "", C: "", D: "" },
                                correctAnswer: "A",
                                feedback: { correct: "", incorrect: "" }
                            });
                            setQuizCache({ ...quizCache, questions: newQ });
                        }}
                        style={{ marginBottom: "24px" }}
                    >
                        + Add Question
                    </button>

                    <div>
                        <button type="button" disabled={hasActiveRequest} onClick={() => void saveQuiz()}>
                            {quizBusy ? "Saving..." : "Save Quiz"}
                        </button>
                    </div>
                </div>
            ) : (
                <div style={{ marginTop: "16px" }}>
                    <h3 style={{ marginBottom: "24px" }}>{courseData.quiz.quizTitle}</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                        {(courseData.quiz.questions || []).map((q: any, i: number) => (
                            <div key={i} className="panel" style={{ margin: 0 }}>
                                <div style={{ display: "flex", gap: "12px", marginBottom: "12px" }}>
                                    <div style={{ background: "var(--primary)", color: "var(--background)", width: "28px", height: "28px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 600, flexShrink: 0 }}>
                                        {i + 1}
                                    </div>
                                    <p style={{ fontWeight: 500, fontSize: "1.05rem", margin: 0, paddingTop: "2px" }}>{q.question}</p>
                                </div>

                                <div className="responsive-indent">
                                    {['A', 'B', 'C', 'D'].map(opt => (
                                        <div key={opt} style={{ marginBottom: "8px", color: q.correctAnswer === opt ? "var(--primary)" : "inherit", fontWeight: q.correctAnswer === opt ? 600 : 400 }}>
                                            <span style={{ display: "inline-block", width: "24px", fontWeight: 600 }}>{opt}.</span>
                                            {q.options?.[opt]} {q.correctAnswer === opt && <span style={{ marginLeft: "8px" }}>✓</span>}
                                        </div>
                                    ))}
                                </div>

                                <div className="responsive-offset">
                                    <div style={{ marginBottom: "6px" }}><strong style={{ color: "var(--primary)" }}>Correct Feedback:</strong> {q.feedback?.correct}</div>
                                    <div><strong style={{ color: "var(--secondary)" }}>Incorrect Feedback:</strong> {q.feedback?.incorrect}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
