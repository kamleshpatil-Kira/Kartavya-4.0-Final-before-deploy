# Course Quality Guidelines (4-Phase Framework)

> This file is the **single source of truth** for how Bhishma generates courses.
> Every course, every module, every question must comply with these rules before it ships.
> These rules are also enforced in the Gemini AI prompts inside `services/gemini_service.py`.

---

## PHASE 1 — BEFORE YOU START

**Know the human before knowing the topic. Design for a specific person.**

| #   | Rule                                                                                                                                                                                              |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 01  | **Know Your Human First, Topic Second.** Design the door before designing what's behind it. A Thanos fan and an OSHA inspector need completely different entry points into the same room.         |
| 02  | **One Audience, One Version — Or Build Multiple.** "Everyone" is nobody. If your audience is too wide, branch the content or build separate modules. Generic kills courses.                       |
| 03  | **Know the Rules of the World Your Course Lives In.** OSHA law. Marvel lore. Coding syntax. Physics. Every course world has rules. Know them exactly and cite them precisely — not approximately. |
| 04  | **Map the Real Stakes Before You Write.** Death. Job loss. Thanos snapping. Failed exam. State the real consequence early. No visible stakes = no learner motivation.                             |

---

## PHASE 2 — WHILE BUILDING

**Structure every lesson. Never abandon the learner.**

| #   | Rule                                                                                                                                                                                                              |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 05  | **Every Lesson Answers What, Why, and What Now.** All three. Every time. No exceptions.                                                                                                                           |
| 06  | **Concrete Before Abstract — Always.** Scene first. Principle second. Rule third. Apply again fourth. Definitions as openers are how people stop paying attention.                                                |
| 07  | **Every Instruction Must Be Executable Without Help.** "Be careful" is not an instruction. A stranger should be able to do it from your words alone, in the real situation you're describing.                     |
| 08  | **Always Include What Happens After It Goes Wrong.** The recovery path is not optional content. It is the most important content. Never abandon the learner at the moment of failure.                             |
| 09  | **Kill Redundancy Before It Ships.** Write one sentence per lesson. If any two sound alike, you have a problem. Merge, cut, or rebuild before writing content.                                                    |
| 10  | **Address the Human Inside the Learner.** Fatigue, rushing, overconfidence, peer pressure — these cause more failures than bad environments. At least one section on internal state is mandatory in every course. |

---

## PHASE 3 — ASSESSMENT

**Tests that certify understanding, not test-taking ability.**

| #   | Rule                                                                                                                                                                                                                 |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11  | **Every Wrong Answer Must Be a Real Mistake.** No joke options. No absurd distractors. If someone can eliminate your wrong answers by being literate with zero subject knowledge, your quiz is certifying ignorance. |
| 12  | **40% of Questions Must Require Application, Not Recall.** Recall fades in 48 hours. Application embeds into behavior. "What is X?" is recall. "What does Jake do when X happens?" is application.                   |
| 13  | **Set a Passing Threshold That Actually Means Something.** Ask which 30% of your content it's acceptable for learners not to know. If the answer is none — raise the bar.                                            |

---

## PHASE 4 — FINISHING

**End with action. Test on a real person.**

| #   | Rule                                                                                                                                                                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 14  | **End With Action, Not a Certificate.** Peak learner engagement is the moment the course ends. Give them 1–3 things to do in the next 24 hours. A congratulations screen is wasted potential.                            |
| 15  | **Test on a Real Target Learner Before It Ships.** Not a colleague. Not yourself. Someone who actually IS the audience. Their confusion is your failure. No course is finished until they've told you what they thought. |

---

## How These Rules Are Enforced in the AI

These quality rules are embedded as **hard requirements** in the Gemini prompt-building methods inside `services/gemini_service.py`:

| Prompt Method                     | Phases Enforced                                                                           |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| `_build_outline_prompt()`         | Phase 1 — stakes, audience precision, world rules                                         |
| `_build_module_content_prompt()`  | Phase 2 — What/Why/What Now, concrete-first, failure recovery, no redundancy, human state |
| `_build_knowledge_check_prompt()` | Phase 3 — application-first, real wrong answers                                           |
| `_build_quiz_prompt()`            | Phase 3 — 40% application ratio, threshold justification                                  |

> **Verbosity rule:** Content must never be padded. Each section must earn its words. The AI is instructed to prefer shorter, clearer sentences over long explanations.
