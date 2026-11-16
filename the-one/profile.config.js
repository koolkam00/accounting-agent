// ─────────────────────────────────────────────────────────────────────────────
//  YOUR PROFILE — this is the only profile on the site, so make it good.
//
//  1. Drop your photos into  public/me/  (JPG/PNG/WebP, portrait 4:5 looks best)
//  2. Point the `photos` list below at them, e.g. "/me/beach.jpg"
//  3. Fill in your name, birthday, prompts and basics
//  4. Restart the server (npm run dev / npm start) to see changes
//
//  Everything marked  EDIT ME  is placeholder copy.
// ─────────────────────────────────────────────────────────────────────────────

export default {
  // Name of the site itself (shows in the logo, browser tab and link previews).
  appName: 'the one',

  // EDIT ME — your first name, as it should appear on your profile.
  name: 'Alex',

  // EDIT ME — used to calculate your age. Format: YYYY-MM-DD
  birthdate: '1998-06-14',

  // How the site refers to you: 'he', 'she' or 'they'.
  pronoun: 'he',

  // EDIT ME — up to 6 photos. The first one is your main photo.
  // Captions are optional. Replace the placeholder illustrations with real photos.
  photos: [
    { src: '/me/placeholder-1.svg', caption: '' },
    { src: '/me/placeholder-2.svg', caption: 'Sunday long run, then pancakes' },
    { src: '/me/placeholder-3.svg', caption: '' },
    { src: '/me/placeholder-4.svg', caption: 'The best tacos in the city. I will die on this hill' },
    { src: '/me/placeholder-5.svg', caption: '' },
    { src: '/me/placeholder-6.svg', caption: '' },
  ],

  // EDIT ME — up to 3 prompts. Write your own questions or pick from
  // src/lib/prompts.js for inspiration. Keep answers short and specific.
  prompts: [
    {
      question: 'A perfect Saturday looks like',
      answer: 'Farmers market at 9, a nap I didn’t plan, and cooking something way too ambitious for two.',
    },
    {
      question: 'My most controversial opinion',
      answer: 'Breakfast for dinner is better than dinner for dinner.',
    },
    {
      question: 'The first date I’d plan',
      answer: 'Cheap dumplings, a long walk with no destination, then a dessert we split but you eat most of.',
    },
  ],

  // EDIT ME — the basics. Delete any line you don't want to show.
  facts: {
    height: '6\'1"',
    location: 'Brooklyn, NY',
    job: 'Product Designer',
    school: 'NYU',
    hometown: 'Chicago, IL',
    lookingFor: 'Something serious',
    drinks: 'Socially',
    smokes: 'Never',
    kids: 'Want someday',
    pets: 'Dog person',
    languages: 'English, bad Spanish',
    sign: 'Gemini',
  },

  // Sign-up rules for visitors.
  signup: {
    // Minimum number of photos someone must add before they can see your profile.
    // Set to 0 to let people in without a photo.
    minPhotos: 1,
  },
};
