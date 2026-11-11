/**
 * Reusable animation definitions and Framer Motion transition variants
 * for 4BIT VoiceCare Patient Terminal.
 */

export const pageVariants = {
  initial: {
    opacity: 0,
    y: 10,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.28,
      ease: 'easeInOut' as const,
    },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: {
      duration: 0.2,
      ease: 'easeInOut' as const,
    },
  },
};

export const stepTransitionVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -16 },
  transition: { duration: 0.3, ease: [0.25, 0.1, 0.25, 1.0] },
};

export const scaleStepVariants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
  transition: { duration: 0.3, ease: [0.25, 0.1, 0.25, 1.0] },
};

export const breathingAuraVariants = {
  animate: {
    scale: [1, 1.08, 1],
    opacity: [0.2, 0.45, 0.2],
  },
  transition: {
    duration: 2.4,
    repeat: Infinity,
    ease: 'easeInOut' as const,
  },
};

export const breathingButtonVariants = {
  animate: {
    scale: [1, 1.025, 1],
  },
  transition: {
    duration: 2.4,
    repeat: Infinity,
    ease: 'easeInOut' as const,
  },
};
