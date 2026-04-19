with open("frontend/src/index.css", "a") as f:
    f.write("""
/* Tailwind Typography (prose) plugin is missing, so adding basic markdown styles manually for Rulebook */
.prose {
  color: #d1d5db;
  line-height: 1.6;
}
.prose h1, .prose h2, .prose h3 {
  color: #34d399;
  font-weight: 700;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}
.prose h1 { font-size: 1.5rem; }
.prose h2 { font-size: 1.25rem; }
.prose h3 { font-size: 1.125rem; }
.prose p { margin-bottom: 1em; }
.prose ul { list-style-type: disc; padding-left: 1.5em; margin-bottom: 1em; }
.prose ol { list-style-type: decimal; padding-left: 1.5em; margin-bottom: 1em; }
.prose li { margin-bottom: 0.25em; }
.prose strong { color: #f3f4f6; font-weight: 600; }
.prose table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
}
.prose th, .prose td {
  border: 1px solid #4b5563;
  padding: 0.5em;
  text-align: left;
}
.prose th { background-color: #1f2937; color: #f3f4f6; }
.prose blockquote {
  border-left: 4px solid #34d399;
  padding-left: 1em;
  color: #9ca3af;
  font-style: italic;
  margin-bottom: 1em;
}
""")
