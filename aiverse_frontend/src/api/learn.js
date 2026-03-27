/**
 * Learn API - Course system endpoints
 */

import api from './axios';

export const learnAPI = {
  listCourses: (params = {}) =>
    api.get('/api/learn/courses/', { params }).then((r) => r.data),

  getCourse: (slug) =>
    api.get(`/api/learn/courses/${slug}/`).then((r) => r.data),

  getLessons: (slug) =>
    api.get(`/api/learn/courses/${slug}/lessons/`).then((r) => r.data),

  getLesson: (courseSlug, lessonSlug) =>
    api
      .get(`/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/`)
      .then((r) => r.data),

  enrollFree: (slug) =>
    api.post(`/api/learn/courses/${slug}/enroll/`).then((r) => r.data),

  getProgress: (slug) =>
    api.get(`/api/learn/courses/${slug}/progress/`).then((r) => r.data),

  updateLessonProgress: (courseSlug, lessonSlug, data) =>
    api
      .post(
        `/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/progress/`,
        data
      )
      .then((r) => r.data),

  completeLesson: (lessonId, data = {}) =>
    api
      .post(`/api/learn/lessons/${lessonId}/complete/`, data)
      .then((r) => r.data),

  createRazorpayOrder: (courseSlug) =>
    api
      .post('/api/learn/payments/razorpay/create-order/', {
        course_slug: courseSlug,
      })
      .then((r) => r.data),

  verifyRazorpayPayment: (data) =>
    api
      .post('/api/learn/payments/razorpay/verify/', data)
      .then((r) => r.data),

  createStripeCheckout: (courseSlug, successUrl, cancelUrl) =>
    api
      .post('/api/learn/payments/create-checkout-session/', {
        course_slug: courseSlug,
        success_url: successUrl,
        cancel_url: cancelUrl,
      })
      .then((r) => r.data),

  createStripeIntent: (courseSlug) =>
    api
      .post('/api/learn/payments/create-intent/', {
        course_slug: courseSlug,
      })
      .then((r) => r.data),

  checkLessonAccess: (courseSlug, lessonSlug) =>
    api
      .get(
        `/api/learn/courses/${courseSlug}/lessons/${lessonSlug}/access/`
      )
      .then((r) => r.data),
};
