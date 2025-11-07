// Impossible CAPTCHA System - For entertainment purposes only!

class ImpossibleCaptcha {
    constructor() {
        this.challenges = [
            {
                type: 'impossible',
                question: 'Enter a number that is both greater than 10 and less than 5.',
                answer: null,
                hint: 'This is mathematically impossible. No number satisfies this condition.'
            },
            {
                type: 'paradox',
                question: 'Type the word that cannot be typed.',
                answer: null,
                hint: 'If you can type it, then it can be typed. Paradox.'
            },
            {
                type: 'logic',
                question: 'Enter the correct answer to this question without entering anything.',
                answer: null,
                hint: 'You must enter something to submit, but the answer requires entering nothing.'
            },
            {
                type: 'temporal',
                question: 'What is today\'s date tomorrow?',
                answer: null,
                hint: 'Tomorrow\'s date cannot be today\'s date.'
            },
            {
                type: 'recursive',
                question: 'Enter the answer that makes this question have no answer.',
                answer: null,
                hint: 'Any answer you provide gives the question an answer.'
            },
            {
                type: 'contradiction',
                question: 'Provide an example of a married bachelor.',
                answer: null,
                hint: 'A bachelor is by definition unmarried. This is a logical contradiction.'
            },
            {
                type: 'impossible',
                question: 'Draw a square circle using only text.',
                answer: null,
                hint: 'A square and a circle are mutually exclusive shapes.'
            },
            {
                type: 'meta',
                question: 'Enter the password to this CAPTCHA without knowing the password.',
                answer: null,
                hint: 'There is no password. But you need to know it to enter it.'
            },
            {
                type: 'logic',
                question: 'Complete this sentence: "This sentence is"',
                answer: null,
                hint: 'Any completion makes the sentence about that completion, creating a paradox.'
            },
            {
                type: 'impossible',
                question: 'Enter a word that rhymes with "orange" perfectly.',
                answer: null,
                hint: 'No common English word rhymes perfectly with orange.'
            }
        ];
        
        this.currentChallenge = null;
        this.attempts = 0;
        this.maxAttempts = 3;
    }
    
    getRandomChallenge() {
        const index = Math.floor(Math.random() * this.challenges.length);
        this.currentChallenge = this.challenges[index];
        return this.currentChallenge;
    }
    
    createCaptchaHTML() {
        const challenge = this.getRandomChallenge();
        
        return `
            <div class="impossible-captcha" id="impossible-captcha">
                <div class="captcha-header">
                    <h3>Security Verification Required</h3>
                    <p class="captcha-subtitle">Please solve this CAPTCHA to continue</p>
                </div>
                
                <div class="captcha-body">
                    <div class="captcha-question">
                        <p class="question-text">${challenge.question}</p>
                    </div>
                    
                    <div class="captcha-input-group">
                        <input 
                            type="text" 
                            id="captcha-answer" 
                            class="captcha-input" 
                            placeholder="Type your answer here..."
                            autocomplete="off"
                        >
                        <button type="button" id="verify-captcha" class="captcha-verify-btn">
                            Verify
                        </button>
                    </div>
                    
                    <div class="captcha-hint">
                        <small>Hint: ${challenge.hint}</small>
                    </div>
                    
                    <div class="captcha-attempts">
                        <small>Attempts remaining: <span id="attempts-remaining">${this.maxAttempts}</span></small>
                    </div>
                    
                    <div class="captcha-error" id="captcha-error" style="display: none;">
                        Incorrect! Try again or consider using OAuth...
                    </div>
                </div>
                
                <div class="captcha-footer">
                    <small style="opacity: 0.6;">
                        This CAPTCHA is intentionally difficult to encourage OAuth usage
                    </small>
                </div>
            </div>
        `;
    }
    
    verify(userAnswer) {
        this.attempts++;
        const attemptsRemaining = this.maxAttempts - this.attempts;
        
        // Update attempts display
        const attemptsEl = document.getElementById('attempts-remaining');
        if (attemptsEl) {
            attemptsEl.textContent = attemptsRemaining;
        }
        
        // Since the answer is null (impossible), any answer is wrong
        // But we'll add a tiny chance (0.1%) for entertainment
        const miracleChance = Math.random() < 0.001;
        
        if (miracleChance) {
            this.showSuccess();
            return true;
        } else {
            this.showError();
            
            if (attemptsRemaining <= 0) {
                this.showFailure();
            } else {
                // Make it even harder - change the question!
                setTimeout(() => {
                    this.regenerateChallenge();
                }, 2000);
            }
            return false;
        }
    }
    
    showError() {
        const errorEl = document.getElementById('captcha-error');
        if (errorEl) {
            errorEl.style.display = 'block';
            errorEl.style.animation = 'shake 0.5s';
            
            setTimeout(() => {
                errorEl.style.animation = '';
            }, 500);
        }
    }
    
    showSuccess() {
        const captchaEl = document.getElementById('impossible-captcha');
        if (captchaEl) {
            captchaEl.innerHTML = `
                <div class="captcha-success">
                    <h3>Congratulations!</h3>
                    <p>You actually solved it! You may now proceed.</p>
                    <p><small>(We're genuinely impressed)</small></p>
                </div>
            `;
            
            // Enable the login button
            const loginBtn = document.querySelector('button[type="submit"]');
            if (loginBtn) {
                loginBtn.disabled = false;
                loginBtn.style.opacity = '1';
            }
        }
    }
    
    showFailure() {
        const captchaEl = document.getElementById('impossible-captcha');
        if (captchaEl) {
            captchaEl.innerHTML = `
                <div class="captcha-failure">
                    <h3>CAPTCHA Failed</h3>
                    <p>That was tough, wasn't it?</p>
                    <p>Consider using OAuth for easier access.</p>
                    <p style="margin-top: 1rem;">
                        <button type="button" id="retry-captcha" class="btn btn--secondary">
                            Try Another CAPTCHA
                        </button>
                    </p>
                </div>
            `;
            
            // Add retry functionality
            document.getElementById('retry-captcha')?.addEventListener('click', () => {
                this.attempts = 0;
                this.restart();
            });
        }
    }
    
    regenerateChallenge() {
        const challenge = this.getRandomChallenge();
        const questionEl = document.querySelector('.question-text');
        const hintEl = document.querySelector('.captcha-hint small');
        
        if (questionEl) {
            questionEl.style.opacity = '0';
            setTimeout(() => {
                questionEl.textContent = challenge.question;
                questionEl.style.opacity = '1';
            }, 300);
        }
        
        if (hintEl) {
            hintEl.innerHTML = `Hint: ${challenge.hint}`;
        }
        
        // Clear input
        const input = document.getElementById('captcha-answer');
        if (input) {
            input.value = '';
            input.focus();
        }
    }
    
    restart() {
        // Remove existing CAPTCHA if it exists
        const existingCaptcha = document.getElementById('impossible-captcha');
        if (existingCaptcha) {
            existingCaptcha.remove();
        }
        
        // Reset attempts
        this.attempts = 0;
        
        // Create new CAPTCHA
        this.init();
    }
    
    init() {
        // Check if CAPTCHA already exists (prevent duplicates)
        const existingCaptcha = document.getElementById('impossible-captcha');
        if (existingCaptcha) {
            return; // Don't create duplicate
        }
        
        // Insert CAPTCHA into the page
        const form = document.querySelector('.login__form');
        if (form) {
            const captchaContainer = document.createElement('div');
            captchaContainer.innerHTML = this.createCaptchaHTML();
            form.insertBefore(captchaContainer.firstElementChild, form.firstElementChild);
            
            // Disable login button until CAPTCHA is solved
            const loginBtn = form.querySelector('button[type="submit"]');
            if (loginBtn) {
                loginBtn.disabled = true;
                loginBtn.style.opacity = '0.5';
                loginBtn.title = 'Solve the CAPTCHA first!';
            }
            
            // Bind verify button
            document.getElementById('verify-captcha')?.addEventListener('click', () => {
                const answer = document.getElementById('captcha-answer')?.value || '';
                this.verify(answer);
            });
            
            // Allow Enter key to verify
            document.getElementById('captcha-answer')?.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const answer = document.getElementById('captcha-answer')?.value || '';
                    this.verify(answer);
                }
            });
        }
    }
}

// Initialize on page load if needed
window.ImpossibleCaptcha = ImpossibleCaptcha;