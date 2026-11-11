/**
 * Reusable animation definitions and Framer Motion transition variants
 * for 4BIT VoiceCare Patient Terminal.
 */

export const heavySpringTransition = {
  type: 'spring' as const,
  stiffness: 100,
  damping: 20,
};

export const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: heavySpringTransition,
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.2,
      ease: 'easeInOut' as const,
    },
  },
};

export const stepTransitionVariants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: heavySpringTransition,
  },
  exit: { opacity: 0, y: -16, transition: { duration: 0.2 } },
};

export const scaleStepVariants = {
  initial: { opacity: 0, y: 20, scale: 0.96 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: heavySpringTransition,
  },
  exit: { opacity: 0, scale: 0.96, transition: { duration: 0.2 } },
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
