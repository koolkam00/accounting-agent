import {
  AtSign, Baby, Briefcase, Cigarette, Coffee, Footprints, GraduationCap, House, Info, Landmark, Languages,
  MapPin, Moon, PawPrint, Ruler, Search, Sparkles, UtensilsCrossed, Wine, BookOpen,
} from 'lucide-react';

/** Prompt questions visitors can answer on their own profile. */
export const PROMPTS = [
  'A perfect Saturday looks like',
  'My most controversial opinion',
  'The first date I’d plan',
  'I’m weirdly good at',
  'Currently obsessed with',
  'Instant green flag',
  'My friends would describe me as',
  'Ask me about',
  'Fastest way to my heart',
  'My go-to karaoke song',
  'Last thing that made me laugh out loud',
  'Unpopular food opinion',
  'I could talk for hours about',
  'Where you’ll find me on a Tuesday night',
  'Dream trip I haven’t taken yet',
  'Best advice I’ve ever gotten',
  'A small thing that makes my whole day',
  'Two things I can’t live without',
];

export const DATE_IDEAS = [
  { id: 'coffee', label: 'Coffee', icon: Coffee },
  { id: 'drinks', label: 'Drinks', icon: Wine },
  { id: 'dinner', label: 'Dinner', icon: UtensilsCrossed },
  { id: 'walk', label: 'A walk', icon: Footprints },
  { id: 'surprise', label: 'Surprise me', icon: Sparkles },
];
export const dateIdea = (id) => DATE_IDEAS.find((d) => d.id === id);

export const FACTS = {
  height: { label: 'Height', icon: Ruler },
  location: { label: 'Lives in', icon: MapPin },
  job: { label: 'Work', icon: Briefcase },
  school: { label: 'School', icon: GraduationCap },
  hometown: { label: 'From', icon: House },
  lookingFor: { label: 'Looking for', icon: Search },
  drinks: { label: 'Drinks', icon: Wine },
  smokes: { label: 'Smokes', icon: Cigarette },
  kids: { label: 'Kids', icon: Baby },
  pets: { label: 'Pets', icon: PawPrint },
  languages: { label: 'Languages', icon: Languages },
  sign: { label: 'Sign', icon: Moon },
  religion: { label: 'Religion', icon: BookOpen },
  politics: { label: 'Politics', icon: Landmark },
  instagram: { label: 'Instagram', icon: AtSign },
};
export const factMeta = (key) => FACTS[key] ?? { label: key, icon: Info };

export const likedWhat = (type) => (type === 'photo' ? 'photo' : type === 'prompt' ? 'answer' : 'profile');
