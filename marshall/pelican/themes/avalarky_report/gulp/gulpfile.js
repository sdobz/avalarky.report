var gulp = require('gulp'),
    sass = require('gulp-sass'),
    rename = require('gulp-rename'),
    minify = require('gulp-minify-css'),
    prefixer = require('gulp-autoprefixer');

gulp.task('sass', function () {
  gulp.src('../scss/source.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(prefixer())
    .pipe(minify())
    .pipe(rename('theme.css'))
    .pipe(gulp.dest('../css'));
});

gulp.task('default', function() {
  gulp.watch('../scss/**/*.scss', ['sass']);
});
