// static/js/dream.js

// Audio context for atmospheric sounds (optional enhancement)
class DreamAudio {
    constructor() {
        this.audioContext = null;
        this.oscillators = [];
        this.enabled = false;
    }
    
    init() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.enabled = true;
        } catch (e) {
            console.log('Audio not supported');
        }
    }
    
    playAtmosphere(type) {
        if (!this.enabled || !this.audioContext) return;
        
        // Stop existing sounds
        this.stop();
        
        const frequencies = {
            peaceful: [220, 277, 330],     // A minor chord
            unsettling: [220, 233, 277],   // Dissonant
            tense: [110, 147, 165],        // Low tension
            terrifying: [55, 62, 73],      // Very low, unsettling
            surreal: [440, 554, 659],      // High, ethereal
            void: [27.5, 32.7, 41.2]       // Sub-bass
        };
        
        const freqs = frequencies[type] || frequencies.peaceful;
        
        freqs.forEach(freq => {
            const osc = this.audioContext.createOscillator();
            const gain = this.audioContext.createGain();
            
            osc.type = 'sine';
            osc.frequency.value = freq;
            
            gain.gain.value = 0.05;
            
            osc.connect(gain);
            gain.connect(this.audioContext.destination);
            
            osc.start();
            this.oscillators.push({ osc, gain });
        });
    }
    
    stop() {
        this.oscillators.forEach(({ osc, gain }) => {
            gain.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.5);
            setTimeout(() => osc.stop(), 500);
        });
        this.oscillators = [];
    }
}

// Visual effects manager
class DreamVisuals {
    constructor() {
        this.container = document.getElementById('dream-container');
    }
    
    distort(level) {
        // Apply CSS filters based on distortion level
        const blur = level * 2;
        const hueRotate = level * 30;
        const contrast = 1 + level * 0.3;
        
        this.container.style.filter = `
            blur(${blur}px) 
            hue-rotate(${hueRotate}deg) 
            contrast(${contrast})
        `;
    }
    
    flashEffect(color = 'white', duration = 100) {
        const flash = document.createElement('div');
        flash.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: ${color};
            opacity: 0.5;
            pointer-events: none;
            z-index: 9999;
        `;
        document.body.appendChild(flash);
        setTimeout(() => flash.remove(), duration);
    }
    
    screenShake(intensity = 5, duration = 500) {
        const start = Date.now();
        const shake = () => {
            const elapsed = Date.now() - start;
            if (elapsed < duration) {
                const x = (Math.random() - 0.5) * intensity;
                const y = (Math.random() - 0.5) * intensity;
                this.container.style.transform = `translate(${x}px, ${y}px)`;
                requestAnimationFrame(shake);
            } else {
                this.container.style.transform = '';
            }
        };
        shake();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.dreamAudio = new DreamAudio();
    window.dreamVisuals = new DreamVisuals();
    
    // Enable audio on first interaction
    document.body.addEventListener('click', () => {
        if (!window.dreamAudio.enabled) {
            window.dreamAudio.init();
        }
    }, { once: true });
});
