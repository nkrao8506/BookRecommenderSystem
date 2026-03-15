'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Navbar from '@/components/Navbar';
import BookCard from '@/components/BookCard';

interface UploadedBook {
  title: string;
  rating: number;
  review: string;
  image: string | null;
}

interface Recommendation {
  title: string;
  author: string;
  image: string;
  match_score?: number;
}

export default function UploadPage() {
  const [bookName, setBookName] = useState('');
  const [rating, setRating] = useState('0');
  const [review, setReview] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadedBook, setUploadedBook] = useState<UploadedBook | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookName) return;

    setLoading(true);
    setError(null);
    setUploadedBook(null);
    setRecommendations([]);

    const formData = new FormData();
    formData.append('book_name', bookName);
    formData.append('rating', rating);
    formData.append('review', review);
    if (image) {
      formData.append('image', image);
    }

    try {
      const res = await fetch('http://127.0.0.1:8000/api/upload/', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (data.error && !data.recommendations?.length) {
        setError(data.error);
      }

      if (data.uploaded_book) {
        setUploadedBook(data.uploaded_book);
      }

      if (data.recommendations) {
        setRecommendations(data.recommendations);
      }
    } catch (err) {
      setError('Failed to upload book. Please try again.');
    }

    setLoading(false);
  };

  const handleReset = () => {
    setBookName('');
    setRating('0');
    setReview('');
    setImage(null);
    setImagePreview(null);
    setUploadedBook(null);
    setRecommendations([]);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <Navbar />

      <main className="pt-24">
        <section className="relative overflow-hidden px-6 py-16 sm:py-24">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-100 via-transparent to-transparent dark:from-emerald-950/30" />

          <div className="mx-auto max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-12 text-center"
            >
              <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
                Add Your
                <span className="block bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                  Favorite Book
                </span>
              </h1>
              <p className="mt-4 text-lg text-zinc-600 dark:text-zinc-400">
                Upload a book you&apos;ve read and get personalized recommendations based on your reading preferences.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
            >
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Book Name *
                    </label>
                    <input
                      type="text"
                      value={bookName}
                      onChange={(e) => setBookName(e.target.value)}
                      placeholder="Enter book title"
                      required
                      className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Your Rating
                    </label>
                    <select
                      value={rating}
                      onChange={(e) => setRating(e.target.value)}
                      className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    >
                      <option value="0">Select rating</option>
                      <option value="5">5 - Excellent</option>
                      <option value="4">4 - Very Good</option>
                      <option value="3">3 - Good</option>
                      <option value="2">2 - Fair</option>
                      <option value="1">1 - Poor</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Your Review
                  </label>
                  <textarea
                    value={review}
                    onChange={(e) => setReview(e.target.value)}
                    placeholder="What did you think about this book?"
                    rows={3}
                    className="w-full rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                    Book Cover Image
                  </label>
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-zinc-300 p-6 transition-colors hover:border-emerald-500 dark:border-zinc-700"
                  >
                    {imagePreview ? (
                      <img
                        src={imagePreview}
                        alt="Preview"
                        className="h-40 w-32 rounded-lg object-cover"
                      />
                    ) : (
                      <>
                        <svg
                          className="mb-3 h-10 w-10 text-zinc-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                          />
                        </svg>
                        <p className="text-sm text-zinc-500">
                          Click to upload book cover
                        </p>
                        <p className="text-xs text-zinc-400">PNG, JPG up to 5MB</p>
                      </>
                    )}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleImageChange}
                      className="hidden"
                    />
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={!bookName || loading}
                    className="flex-1 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-3 font-semibold text-white transition-all hover:from-emerald-700 hover:to-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg
                          className="h-5 w-5 animate-spin"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Analyzing...
                      </span>
                    ) : (
                      'Get Recommendations'
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="rounded-xl border border-zinc-200 bg-white px-6 py-3 font-medium text-zinc-700 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
                  >
                    Reset
                  </button>
                </div>
              </form>
            </motion.div>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-200"
                >
                  <p>{error}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {uploadedBook && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="mt-8"
              >
                <h2 className="mb-6 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
                  Your Uploaded Book
                </h2>
                <div className="flex gap-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-md dark:border-zinc-800 dark:bg-zinc-900">
                  {uploadedBook.image && (
                    <img
                      src={`http://127.0.0.1:8000${uploadedBook.image}`}
                      alt={uploadedBook.title}
                      className="h-40 w-32 flex-shrink-0 rounded-lg object-cover"
                    />
                  )}
                  <div className="flex flex-col justify-center">
                    <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                      {uploadedBook.title}
                    </h3>
                    {uploadedBook.rating > 0 && (
                      <div className="mt-2 flex items-center gap-1">
                        {[...Array(5)].map((_, i) => (
                          <svg
                            key={i}
                            className={`h-5 w-5 ${
                              i < uploadedBook.rating
                                ? 'fill-amber-400 text-amber-400'
                                : 'fill-zinc-200 text-zinc-200'
                            }`}
                            viewBox="0 0 20 20"
                          >
                            <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                          </svg>
                        ))}
                      </div>
                    )}
                    {uploadedBook.review && (
                      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                        &quot;{uploadedBook.review}&quot;
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {recommendations.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="mt-8"
              >
                <div className="mb-6 flex items-center gap-3">
                  <span className="flex h-3 w-3 rounded-full bg-emerald-500" />
                  <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
                    Books You Might Also Like
                  </h2>
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {recommendations.map((book, index) => (
                    <BookCard
                      key={`${book.title}-${index}`}
                      title={book.title}
                      author={book.author}
                      image={book.image}
                      index={index}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
