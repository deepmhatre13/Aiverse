import api from './axios';

let lessonCache = null;

export const getCourses = () => api.get('/api/learn/courses/');

export const getCourseLessons = (courseSlug) =>
  api.get(`/api/learn/courses/${courseSlug}/lessons/`);

export const getLessonDetail = (courseSlug, lessonSlug) =>
  api.get(`/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/`);

export const getLessonQuiz = (courseSlug, lessonSlug) =>
  api.get(`/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/quiz/`);

export const submitLessonQuiz = (courseSlug, lessonSlug, payload) =>
  api.post(`/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/quiz/submit/`, payload);

export const getEnrollments = () => api.get('/api/learn/enrollments/');

/** Resolve lesson id → { course, lesson } by scanning published courses */
export async function findLessonById(lessonId) {
  const id = Number(lessonId);
  if (lessonCache?.[id]) return lessonCache[id];

  const coursesRes = await getCourses();
  const courses = Array.isArray(coursesRes.data)
    ? coursesRes.data
    : coursesRes.data?.results || [];

  for (const course of courses) {
    try {
      const lessonsRes = await getCourseLessons(course.slug);
      const lessons = lessonsRes.data?.lessons || lessonsRes.data || [];
      const lesson = lessons.find((l) => l.id === id);
      if (lesson) {
        const result = { course, lesson };
        lessonCache = { ...(lessonCache || {}), [id]: result };
        return result;
      }
    } catch {
      // skip inaccessible courses
    }
  }
  return null;
}

/** Transform backend MCQ to UI-friendly question shape */
export function normalizeQuizQuestions(questions = []) {
  return questions.map((q) => ({
    id: q.id,
    question_text: q.question,
    options: [
      { id: 'A', text: q.option_a },
      { id: 'B', text: q.option_b },
      { id: 'C', text: q.option_c },
      { id: 'D', text: q.option_d },
    ].filter((o) => o.text),
  }));
}
