import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        globals: true,
        include: ['test/**/*.test.js'],
        setupFiles: ['test/setup.js'],
    },
});
