let currentModule = 0;
let totalModules = 0;
let knowledgeChecksCompleted = {};
let quizAnswers = {};
let modulesCompleted = {}; // Track which modules are completed

// Section-level tracking (RISE 365: Continue button after each section)
let currentSection = { module: 0, section: 0 };
let sectionsCompleted = {}; // Track completed sections: "module.section"
let sectionAudioPlayed = {}; // Track if audio finished for each section: "module.section"
let sectionContentViewed = {}; // Track if content viewed for each section: "module.section"


// xAPI Initialization State
let xapiInitialized = false;
let courseURI = "";
let registrationId = "";
let xapiEndpoint = "";
let xapiAuth = "";
let xapiActor = null;

// LMS-specific Launch Parameters (EmpowerLMS / Hygiena)
let lmsSubscriptionId = "";
let lmsStudentID = "";
let lmsPortalId = "";
let lmsIdentifier = "";


// LMS Bookmark state (for resume from LMS via State API)
var lmsBookmark = null;
var bookmarkLoading = false;
var bookmarkLoaded = false;
var _isResuming = false;

// Module-level completion tracking (used in showModule/checkModuleCompletion)
var moduleCompletionStatus = {};
var audioPlayed = {};
var contentScrolled = {};

// Track the last visited section per module (so sidebar nav resumes where you left off)
var lastModuleSection = {};

// Track quiz state so sidebar nav can resume from the right place
// Values: 'none' | 'intro' | 'active' | 'results'
var quizState = 'none';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize xAPI connection
    initXAPI();
    
    // Load bookmark from LRS for auto-resume on LMS re-launch
    if (xapiInitialized && xapiEndpoint) {
        bookmarkLoading = true;
        loadBookmarkFromLRS(function(bookmark) {
            bookmarkLoading = false;
            bookmarkLoaded = true;
            if (bookmark && bookmark.currentModule > 0) {
                lmsBookmark = bookmark;
                console.log('LMS Bookmark loaded: Module ' + bookmark.currentModule + ', Section ' + bookmark.currentSection);
                // Auto-resume if course has not started yet (LMS re-launch behavior)
                if (!window.courseStarted) {
                    console.log('Auto-resuming from LMS bookmark...');
                    resumeFromBookmark(bookmark);
                }
            } else {
                console.log('No bookmark found in LRS - fresh course');
            }
        });
    } else {
        bookmarkLoaded = true;
    }
    
    totalModules = document.querySelectorAll('.module-section').length;
    
    // Ensure all sections are hidden initially - only shown after Start Course is clicked
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Initialize section completion tracking
    // All sections start with Continue button disabled until audio completes and content is viewed
    document.querySelectorAll('.content-section').forEach(section => {
        const sectionId = section.id;
        const matches = sectionId.match(/module-(\\d+)-section-(\\d+)/);
        if (matches) {
            const moduleNum = parseInt(matches[1]);
            const sectionNum = parseInt(matches[2]);
            const sectionKey = `${moduleNum}.${sectionNum}`;
            sectionAudioPlayed[sectionKey] = false;
            sectionContentViewed[sectionKey] = false;
            
            // Set up audio completion tracking
            const audio = section.querySelector('audio');
            if (audio) {
                const checkAudioComplete = () => {
                    sectionAudioPlayed[sectionKey] = true;
                    checkSectionCompletion(moduleNum, sectionNum);
                };
                
                audio.addEventListener('ended', checkAudioComplete, { once: true });
                
                // For chunked audio, track when all chunks are done
                if (audio.hasAttribute('data-chunked')) {
                    // Track chunk completion via global function if available
                    const audioId = audio.id;
                    const originalLoadNext = window['loadNextChunk_' + moduleNum + '_' + sectionNum];
                    if (originalLoadNext) {
                        let chunkCount = 0;
                        const maxChunks = parseInt(audio.getAttribute('data-total-chunks') || '1');
                        window['loadNextChunk_' + moduleNum + '_' + sectionNum] = function() {
                            originalLoadNext();
                            chunkCount++;
                            if (chunkCount >= maxChunks) {
                                checkAudioComplete();
                            }
                        };
                    }
                }
            } else {
                // No audio - mark as played immediately
                sectionAudioPlayed[sectionKey] = true;
            }
            
            // Set up scroll tracking to detect content viewing
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        sectionContentViewed[sectionKey] = true;
                        checkSectionCompletion(moduleNum, sectionNum);
                    }
                });
            }, { threshold: 0.8 }); // Consider viewed when 80% scrolled
            
            observer.observe(section);
        }
    });
});

function checkSectionCompletion(moduleNum, sectionNum) {
    const sectionKey = `${moduleNum}.${sectionNum}`;
    const audioPlayed = sectionAudioPlayed[sectionKey] || false;
    const contentViewed = sectionContentViewed[sectionKey] || false;
    
    // Sync global tracker state to inline tracker (Change 5b)
    const trackingKey = 'section_' + moduleNum + '_' + sectionNum + '_tracking';
    if (window[trackingKey]) {
        if (audioPlayed) window[trackingKey].audioCompleted = true;
        if (contentViewed) window[trackingKey].contentViewed = true;
    }
    
    // Get the module data to check if this is the last section
    const moduleData = window.courseData?.modules?.[moduleNum - 1];
    const contentData = moduleData?.content;
    const sections = contentData?.sections || [];
    const totalSections = sections.length;
    const isLastSection = sectionNum === totalSections;
    
    // For the last section, also check knowledge check completion
    let knowledgeCheckPassed = true; // Default to true if no KC
    if (isLastSection && moduleData?.knowledgeCheck) {
        knowledgeCheckPassed = knowledgeChecksCompleted[moduleNum] || false;
        // Also sync KC state to inline tracker
        if (window[trackingKey]) {
            window[trackingKey].kcCompleted = knowledgeCheckPassed;
        }
    }
    
    // Enable Continue button when all requirements are met
    const continueButton = document.getElementById(`continue-${moduleNum}-${sectionNum}`);
    if (continueButton) {
        const allComplete = audioPlayed && contentViewed && knowledgeCheckPassed;
        if (allComplete) {
            continueButton.disabled = false;
            continueButton.classList.remove('disabled');
            continueButton.style.opacity = '1';
            continueButton.style.cursor = 'pointer';
            continueButton.style.pointerEvents = 'auto';
            
            // Send xAPI Completed statement if this is the last section of the module
            if (isLastSection && !modulesCompleted[moduleNum]) {
                modulesCompleted[moduleNum] = true;
                
                // Update sidebar if function exists (it's called updateSidebarProgress locally in other parts)
                // But we'll just focus on xAPI here
                
                if (xapiInitialized) {
                    const moduleTitle = moduleData?.title || `Module ${moduleNum}`;
                    const moduleID = courseURI + "/module/" + moduleNum;
                    sendStatement(VERBS.completed, moduleID, moduleTitle, "Learner completed module " + moduleNum, null, null, "http://adlnet.gov/expapi/activities/module");
                    console.log(`Module ${moduleNum} completed`);
                }
            }
        } else {
            continueButton.disabled = true;
            continueButton.classList.add('disabled');
        }
    }
}


// xAPI Helper Functions
// Helper to get URL query parameter
function getUrlParam(name) {
    var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\\+/g, ' '));
}

function initXAPI() {
    try {
        console.log("Initializing xAPI...");
        
        // Read ALL parameters directly from the URL (most reliable method)
        xapiEndpoint = getUrlParam('endpoint');
        xapiAuth = getUrlParam('auth');
        registrationId = getUrlParam('registration');
        var actorParam = getUrlParam('actor');
        var activityIdParam = getUrlParam('activity_id');
        var groupingParam = getUrlParam('grouping');
        
        // Parse LMS-specific parameters from URL
        lmsSubscriptionId = getUrlParam('subscriptionId') || "";
        lmsStudentID = getUrlParam('studentID') || "";
        lmsPortalId = getUrlParam('portalId') || "";
        lmsIdentifier = getUrlParam('identifier') || "";
        
        console.log("LMS Params parsed:", { 
            subscriptionId: lmsSubscriptionId ? "present" : "missing",
            studentID: lmsStudentID ? "present" : "missing",
            portalId: lmsPortalId ? "present" : "missing",
            identifier: lmsIdentifier
        });

        
        if (xapiEndpoint) {
            console.log("LRS Endpoint found:", xapiEndpoint);
            
            // Parse actor from URL
            if (actorParam) {
                try {
                    xapiActor = JSON.parse(actorParam);
                    // CRITICAL: Normalize actor fields
                    // SCORM Cloud sends arrays (name:["k p"], account:[{...}])
                    // but xAPI spec requires strings/objects
                    if (Array.isArray(xapiActor.name)) {
                        xapiActor.name = xapiActor.name[0] || "";
                    }
                    if (Array.isArray(xapiActor.account)) {
                        xapiActor.account = xapiActor.account[0] || {};
                    }
                    if (Array.isArray(xapiActor.mbox)) {
                        xapiActor.mbox = xapiActor.mbox[0] || "";
                    }
                    if (Array.isArray(xapiActor.mbox_sha1sum)) {
                        xapiActor.mbox_sha1sum = xapiActor.mbox_sha1sum[0] || "";
                    }
                    if (Array.isArray(xapiActor.openid)) {
                        xapiActor.openid = xapiActor.openid[0] || "";
                    }
                    // CRITICAL: Rename SCORM Cloud's non-standard account field names
                    // SCORM Cloud sends: accountServiceHomePage, accountName
                    // xAPI spec requires: homePage, name
                    if (xapiActor.account && typeof xapiActor.account === 'object') {
                        if (xapiActor.account.accountServiceHomePage && !xapiActor.account.homePage) {
                            xapiActor.account.homePage = xapiActor.account.accountServiceHomePage;
                            delete xapiActor.account.accountServiceHomePage;
                        }
                        if (xapiActor.account.accountName && !xapiActor.account.name) {
                            xapiActor.account.name = xapiActor.account.accountName;
                            delete xapiActor.account.accountName;
                        }
                    }
                    console.log("Actor parsed and normalized:", JSON.stringify(xapiActor));
                } catch(e) {
                    console.warn("Failed to parse actor:", e);
                }
            }
            
            // Log registration ID
            if (registrationId) {
                console.log("Registration ID:", registrationId);
            } else {
                console.warn("No registration ID found in URL");
            }
            
            // Set Course URI from activity_id (MUST match tincan.xml)
            courseURI = activityIdParam || window.location.href.split('?')[0];
            if (courseURI.endsWith('index.html')) {
                courseURI = courseURI.substring(0, courseURI.length - 10);
            }
            if (courseURI.endsWith('/')) {
                courseURI = courseURI.substring(0, courseURI.length - 1);
            }
            
            console.log("Course URI:", courseURI);
            console.log("Auth present:", !!xapiAuth);
            xapiInitialized = true;
            console.log("xAPI initialized successfully!");
        } else {
            console.warn("No LRS endpoint found in URL. xAPI disabled (Standalone Mode).");
            xapiInitialized = false;
            // Prevent ADL wrapper from sending to a default relative path
            if (typeof ADL !== 'undefined' && ADL.XAPIWrapper) {
                ADL.XAPIWrapper.changeConfig({ endpoint: null });
            }
        }
    } catch(e) {
        console.error("Failed to initialize xAPI:", e);
    }
}

function generateUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}


function sendStatement(verb, objectId, objectName, description, score, response, activityType) {
    if (!xapiInitialized) return;
    
    try {
        // Build actor (from URL params)
        var actor = xapiActor;
        if (!actor) {
            actor = {"mbox": "mailto:unknown@example.com", "name": "Unknown Learner"};
        }
        
        // Build the statement
        var stmt = {
            "actor": actor,
            "verb": {
                "id": verb.id,
                "display": verb.display
            },
            "object": {
                "id": objectId,
                "objectType": "Activity",
                "definition": {
                    "name": { "en-US": objectName }
                }
            },
            "timestamp": new Date().toISOString()
        };
        
        // Add activity type (Rise360 compatible: course, module, assessment, etc.)
        if (activityType) {
            stmt.object.definition.type = activityType;
        }
        
        // Add description
        if (description) {
            stmt.object.definition.description = { "en-US": description };
        }
        
        // CRITICAL: Add context with registration ID
        // This links the statement to the learner's course attempt in the LMS
        stmt.context = {};
        if (registrationId) {
            stmt.context.registration = registrationId;
        }
        
        // LMS-specific fields (EmpowerLMS / Hygiena requirement)
        // These must be top-level fields in the statement
        if (lmsPortalId) stmt.portalId = lmsPortalId;
        if (lmsStudentID) stmt.studentID = lmsStudentID;
        if (lmsSubscriptionId) stmt.subscriptionId = lmsSubscriptionId;
        if (lmsIdentifier) stmt.identifier = lmsIdentifier;
        
        // Ensure statementId is present (some LMSs require it)
        if (!stmt.id) {
            stmt.id = generateUUID();
        }
        stmt.statementId = stmt.id; // redundant but safe for some LMSs

        // Add grouping context so LMS knows which course this belongs to
        stmt.context.contextActivities = {
            "grouping": [{
                "id": courseURI,
                "objectType": "Activity"
            }]
        };
        
        // Add result if score or response provided
        if (score !== null && score !== undefined) {
            if (!stmt.result) stmt.result = {};
            stmt.result.score = {
                "raw": score,
                "min": 0,
                "max": 100,
                "scaled": score / 100
            };
        }
        if (response !== null && response !== undefined) {
            if (!stmt.result) stmt.result = {};
            stmt.result.response = String(response);
        }
        
        // Add success/completion status based on verb
        if (verb.id === "http://adlnet.gov/expapi/verbs/passed") {
            if (!stmt.result) stmt.result = {};
            stmt.result.success = true;
            stmt.result.completion = true;
        } else if (verb.id === "http://adlnet.gov/expapi/verbs/failed") {
            if (!stmt.result) stmt.result = {};
            stmt.result.success = false;
            stmt.result.completion = true;
        } else if (verb.id === "http://adlnet.gov/expapi/verbs/completed") {
            if (!stmt.result) stmt.result = {};
            stmt.result.completion = true;
        }
        
        // Send via ADL xAPIWrapper (official library handles auth, headers)
        if (typeof ADL !== 'undefined' && ADL.XAPIWrapper && ADL.XAPIWrapper.testConfig()) {
            ADL.XAPIWrapper.sendStatement(stmt, function(resp, obj) {
                if (resp && resp.status >= 200 && resp.status < 300) {
                    console.log("xAPI Statement Sent via ADL: " + verb.display["en-US"] + " (HTTP " + resp.status + ")");
                } else {
                    console.error("xAPI Statement FAILED via ADL: HTTP " + (resp ? resp.status : '?') + " - " + (resp ? resp.responseText : 'no response'));
                }
            });
            console.log("xAPI statement sent via ADL wrapper:", stmt);
        } else if (xapiEndpoint) {
            // Fallback: direct XHR if ADL wrapper not available
            var xhr = new XMLHttpRequest();
            var stmtUrl = xapiEndpoint + "statements";
            xhr.open("POST", stmtUrl, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.setRequestHeader("X-Experience-API-Version", "1.0.3");
            if (xapiAuth) {
                xhr.setRequestHeader("Authorization", xapiAuth);
            }

            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log("xAPI Statement Sent (fallback): " + verb.display["en-US"] + " (HTTP " + xhr.status + ")");
                    } else {
                        console.error("xAPI Statement FAILED (fallback): HTTP " + xhr.status + " - " + xhr.responseText);
                    }
                }
            };
            xhr.send(JSON.stringify(stmt));
            console.log("xAPI statement sent (fallback XHR):", stmt);
        } else {
            console.warn("No xAPI endpoint or ADL wrapper configured");
        }
        
        // Also send to State API for LMS compatibility (EmpowerLMS / Hygiena)
        // This LMS expects state data via PUT to /activities/state
        if (xapiEndpoint) {
            try {
                // Construct State API URL
                // Note: The LMS uses a specific query string format
                var stateUrl = xapiEndpoint + "activities/state";
                var queryParams = [];
                
                queryParams.push("stateId=cumulative_time"); // Using cumulative_time as seen in logs
                queryParams.push("activityId=" + encodeURIComponent(courseURI));
                queryParams.push("agent=" + encodeURIComponent(JSON.stringify(actor)));
                
                if (registrationId) queryParams.push("registration=" + encodeURIComponent(registrationId));
                if (lmsSubscriptionId) queryParams.push("subscriptionId=" + encodeURIComponent(lmsSubscriptionId));
                if (lmsStudentID) queryParams.push("studentID=" + encodeURIComponent(lmsStudentID));
                if (lmsPortalId) queryParams.push("portalId=" + encodeURIComponent(lmsPortalId));
                if (lmsIdentifier) queryParams.push("identifier=" + encodeURIComponent(lmsIdentifier));
                
                stateUrl += "?" + queryParams.join("&");
                
                // Create simple state payload (suspend_data format)
                // The LMS seems to want {v: 2, d: ...}
                var stateData = {
                    v: 2,
                    d: [100, 111, 110, 101] // Dummy data for now, just to satisfy the call
                };
                
                var stateXhr = new XMLHttpRequest();
                stateXhr.open("PUT", stateUrl, true);
                stateXhr.setRequestHeader("Content-Type", "application/json");
                stateXhr.setRequestHeader("X-Experience-API-Version", "1.0.3");
                if (xapiAuth) {
                    stateXhr.setRequestHeader("Authorization", xapiAuth);
                }
                
                stateXhr.onreadystatechange = function() {
                    if (stateXhr.readyState === 4) {
                        if (stateXhr.status >= 200 && stateXhr.status < 300) {
                            console.log("State API Update Success");
                        } else {
                            console.warn("State API Update Failed: " + stateXhr.status);
                        }
                    }
                };
                stateXhr.send(JSON.stringify(stateData));
            } catch(e) {
                console.error("Error sending State API update:", e);
            }
        }

        
    } catch(e) {
        console.error("Error sending xAPI statement:", e);
    }
}

// xAPI Verbs
const VERBS = {
    initialized: {
        id: "http://adlnet.gov/expapi/verbs/initialized",
        display: { "en-US": "initialized" }
    },
    completed: {
        id: "http://adlnet.gov/expapi/verbs/completed",
        display: { "en-US": "completed" }
    },
    passed: {
        id: "http://adlnet.gov/expapi/verbs/passed",
        display: { "en-US": "passed" }
    },
    failed: {
        id: "http://adlnet.gov/expapi/verbs/failed",
        display: { "en-US": "failed" }
    },
    experienced: {
        id: "http://adlnet.gov/expapi/verbs/experienced",
        display: { "en-US": "experienced" }
    },
    scored: {
        id: "http://adlnet.gov/expapi/verbs/scored",
        display: { "en-US": "scored" }
    },
    attempted: {
        id: "http://adlnet.gov/expapi/verbs/attempted",
        display: { "en-US": "attempted" }
    },
    progressed: {
        id: "http://adlnet.gov/expapi/verbs/progressed",
        display: { "en-US": "progressed" }
    },
    terminated: {
        id: "http://adlnet.gov/expapi/verbs/terminated",
        display: { "en-US": "terminated" }
    }
};

function startCourse() {
    // If bookmark is still loading from LRS, wait for it (max 3 seconds)
    if (bookmarkLoading && !bookmarkLoaded) {
        console.log('Waiting for LRS bookmark to load before starting...');
        var waitCount = 0;
        var waitInterval = setInterval(function() {
            waitCount++;
            if (bookmarkLoaded || waitCount > 30) {
                clearInterval(waitInterval);
                if (waitCount > 30) {
                    console.warn('Bookmark load timed out after 3s - starting fresh');
                    bookmarkLoading = false;
                    bookmarkLoaded = true;
                }
                // Check if bookmark arrived while we were waiting
                if (lmsBookmark && lmsBookmark.currentModule > 0) {
                    resumeFromBookmark(lmsBookmark);
                } else {
                    _doStartCourse();
                }
            }
        }, 100);
        return;
    }
    // Check if bookmark already loaded (auto-resume may have already fired)
    if (lmsBookmark && lmsBookmark.currentModule > 0 && !window.courseStarted) {
        resumeFromBookmark(lmsBookmark);
        return;
    }
    _doStartCourse();
}

function _doStartCourse() {
    try {
        // Send Attempted statement (changed from initialized as per requirements)
        if (xapiInitialized) {
            sendStatement(VERBS.attempted, courseURI, document.title, "Learner attempted the course.", null, null, "http://adlnet.gov/expapi/activities/course");
        }

        // Hide home screen
        const homeScreen = document.getElementById('homeScreen');
        if (homeScreen) {
            homeScreen.style.display = 'none';
        }
        
        // Show Course Instructions section first
        const instructionsSection = document.getElementById('courseInstructionsSection');
        if (instructionsSection) {
            instructionsSection.style.display = 'block';
            window.scrollTo(0, 0);
            
            // Set up audio completion tracking for instructions
            const instructionsAudio = document.getElementById('instructions-audio');
            if (instructionsAudio) {
                // Start audio playback when instructions are shown
                // IMPORTANT: Only ONE autoplay attempt to avoid race conditions
                // that trigger the anti-seeking script and stall at ~2 seconds
                const playAudio = () => {
                    const playPromise = instructionsAudio.play();
                    if (playPromise !== undefined) {
                        playPromise.catch(e => {
                            console.log('Autoplay prevented, will allow manual play:', e);
                        });
                    }
                };
                
                // Check if audio file exists by trying to load it
                let audioLoaded = false;
                let audioError = false;
                
                // Track when audio loads successfully
                instructionsAudio.addEventListener('loadeddata', function() {
                    audioLoaded = true;
                    console.log('Instructions audio loaded successfully');
                }, { once: true });
                
                // Track when audio completes
                instructionsAudio.addEventListener('ended', function() {
                    unlockInstructionsNavigation();
                }, { once: true });
                
                // Handle audio load error (if file doesn't exist)
                instructionsAudio.addEventListener('error', function() {
                    audioError = true;
                    console.log('Instructions audio not found or failed to load');
                    // Enable continue button immediately if audio fails
                    unlockInstructionsNavigation();
                }, { once: true });
                
                // Single autoplay attempt with a reasonable delay
                setTimeout(() => {
                    playAudio();
                }, 300);
                
                // Fallback: If audio doesn't load within 4 seconds, enable continue
                setTimeout(() => {
                    if (!audioLoaded && !audioError) {
                        // Check if audio actually has a source
                        const source = instructionsAudio.querySelector('source');
                        if (source && source.src) {
                            // Check readyState without re-loading
                            if (instructionsAudio.readyState === 0 || instructionsAudio.networkState === 3) {
                                console.log('Audio file not found, enabling continue');
                                unlockInstructionsNavigation();
                            }
                        } else {
                            // No audio source - enable continue
                            unlockInstructionsNavigation();
                        }
                    }
                }, 4000);
                
                // Additional fallback: Enable continue after 6 seconds regardless
                setTimeout(() => {
                    var lockMsg = document.getElementById('instructionsLockMsg');
                    if (lockMsg && lockMsg.style.display !== 'none') {
                        console.log('Timeout reached, enabling continue button');
                        enableInstructionsContinue();
                    }
                }, 6000);
            } else {
                // No audio element - unlock immediately
                setTimeout(() => {
                    unlockInstructionsNavigation();
                }, 1000);
            }
        } else {
            // If instructions section doesn't exist, proceed directly to modules
            proceedToFirstModule();
        }
    } catch (error) {
        console.error('Error in startCourse:', error);
        alert(window.uiLabels.error_refresh);
    }
}

// ========== RESUME / PROGRESS PERSISTENCE ==========
// Save course progress to localStorage
function saveCourseProgress() {
    try {
        var courseKey = 'kartavya_progress_' + (document.title || 'course').replace(/[^a-zA-Z0-9]/g, '_');
        var progressData = {
            currentModule: currentModule,
            currentSection: currentSection,
            modulesCompleted: JSON.parse(JSON.stringify(modulesCompleted || {})),
            knowledgeChecksCompleted: JSON.parse(JSON.stringify(knowledgeChecksCompleted || {})),
            sectionsCompleted: JSON.parse(JSON.stringify(sectionsCompleted || {})),
            quizRetryCount: quizRetryCount || 0,
            savedAt: new Date().toISOString()
        };
        localStorage.setItem(courseKey, JSON.stringify(progressData));
        console.log('Progress saved: Module ' + currentModule + ', Section ' + (currentSection?.section || 1));
    } catch(e) {
        console.warn('Could not save progress:', e);
    }
    // Also save bookmark to LRS for LMS resume support
    saveBookmarkToLRS();
}

// Load course progress from localStorage
function getCourseProgress() {
    try {
        var courseKey = 'kartavya_progress_' + (document.title || 'course').replace(/[^a-zA-Z0-9]/g, '_');
        var saved = localStorage.getItem(courseKey);
        if (saved) {
            var data = JSON.parse(saved);
            // Return current module/section for display (handle both object and number formats)
            return {
                currentModule: data.currentModule || 1,
                currentSection: (typeof data.currentSection === 'object') ? (data.currentSection.section || 1) : (data.currentSection || 1),
                modulesCompleted: data.modulesCompleted || {},
                knowledgeChecksCompleted: data.knowledgeChecksCompleted || {},
                sectionsCompleted: data.sectionsCompleted || {},
                quizRetryCount: data.quizRetryCount || 0,
                savedAt: data.savedAt
            };
        }
    } catch(e) {
        console.warn('Could not load progress:', e);
    }
    return null;
}

// Clear saved progress (on course completion)
function clearCourseProgress() {
    try {
        var courseKey = 'kartavya_progress_' + (document.title || 'course').replace(/[^a-zA-Z0-9]/g, '_');
        localStorage.removeItem(courseKey);
        console.log('Saved progress cleared');
    } catch(e) {
        console.warn('Could not clear progress:', e);
    }
    // Also delete bookmark from LRS
    deleteBookmarkFromLRS();
    lmsBookmark = null;
}

// ========== LRS BOOKMARK FUNCTIONS (State API) ==========
// Save bookmark to LRS via xAPI State API
function saveBookmarkToLRS() {
    if (!xapiInitialized || !xapiEndpoint) return;
    try {
        var bookmarkData = {
            currentModule: currentModule,
            currentSection: (typeof currentSection === 'object') ? currentSection.section : currentSection,
            modulesCompleted: modulesCompleted || {},
            knowledgeChecksCompleted: knowledgeChecksCompleted || {},
            sectionsCompleted: sectionsCompleted || {},
            quizRetryCount: quizRetryCount || 0,
            timestamp: new Date().toISOString()
        };
        var actor = xapiActor || {"mbox": "mailto:unknown@example.com"};
        var stateUrl = xapiEndpoint + 'activities/state';
        var queryParams = [
            'stateId=bookmark',
            'activityId=' + encodeURIComponent(courseURI),
            'agent=' + encodeURIComponent(JSON.stringify(actor))
        ];
        if (registrationId) queryParams.push('registration=' + encodeURIComponent(registrationId));
        if (lmsSubscriptionId) queryParams.push('subscriptionId=' + encodeURIComponent(lmsSubscriptionId));
        if (lmsStudentID) queryParams.push('studentID=' + encodeURIComponent(lmsStudentID));
        if (lmsPortalId) queryParams.push('portalId=' + encodeURIComponent(lmsPortalId));
        if (lmsIdentifier) queryParams.push('identifier=' + encodeURIComponent(lmsIdentifier));
        stateUrl += '?' + queryParams.join('&');
        var xhr = new XMLHttpRequest();
        xhr.open('PUT', stateUrl, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-Experience-API-Version', '1.0.3');
        if (xapiAuth) xhr.setRequestHeader('Authorization', xapiAuth);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status >= 200 && xhr.status < 300) {
                    console.log('Bookmark saved to LRS: Module ' + bookmarkData.currentModule + ', Section ' + bookmarkData.currentSection);
                } else {
                    console.warn('Bookmark save failed: HTTP ' + xhr.status);
                }
            }
        };
        xhr.send(JSON.stringify(bookmarkData));
    } catch(e) {
        console.error('Error saving bookmark to LRS:', e);
    }
}

// Load bookmark from LRS via xAPI State API
function loadBookmarkFromLRS(callback) {
    if (!xapiInitialized || !xapiEndpoint) {
        if (callback) callback(null);
        return;
    }
    try {
        var actor = xapiActor || {"mbox": "mailto:unknown@example.com"};
        var stateUrl = xapiEndpoint + 'activities/state';
        var queryParams = [
            'stateId=bookmark',
            'activityId=' + encodeURIComponent(courseURI),
            'agent=' + encodeURIComponent(JSON.stringify(actor))
        ];
        if (registrationId) queryParams.push('registration=' + encodeURIComponent(registrationId));
        if (lmsSubscriptionId) queryParams.push('subscriptionId=' + encodeURIComponent(lmsSubscriptionId));
        if (lmsStudentID) queryParams.push('studentID=' + encodeURIComponent(lmsStudentID));
        if (lmsPortalId) queryParams.push('portalId=' + encodeURIComponent(lmsPortalId));
        if (lmsIdentifier) queryParams.push('identifier=' + encodeURIComponent(lmsIdentifier));
        stateUrl += '?' + queryParams.join('&');
        var xhr = new XMLHttpRequest();
        xhr.open('GET', stateUrl, true);
        xhr.setRequestHeader('X-Experience-API-Version', '1.0.3');
        if (xapiAuth) xhr.setRequestHeader('Authorization', xapiAuth);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status >= 200 && xhr.status < 300 && xhr.responseText) {
                    try {
                        var bookmark = JSON.parse(xhr.responseText);
                        console.log('Bookmark loaded from LRS:', bookmark);
                        if (callback) callback(bookmark);
                    } catch(e) {
                        console.warn('Could not parse bookmark:', e);
                        if (callback) callback(null);
                    }
                } else {
                    console.log('No bookmark in LRS (HTTP ' + xhr.status + ')');
                    if (callback) callback(null);
                }
            }
        };
        xhr.send();
    } catch(e) {
        console.error('Error loading bookmark from LRS:', e);
        if (callback) callback(null);
    }
}

// Delete bookmark from LRS (on course completion)
function deleteBookmarkFromLRS() {
    if (!xapiInitialized || !xapiEndpoint) return;
    try {
        var actor = xapiActor || {"mbox": "mailto:unknown@example.com"};
        var stateUrl = xapiEndpoint + 'activities/state';
        var queryParams = [
            'stateId=bookmark',
            'activityId=' + encodeURIComponent(courseURI),
            'agent=' + encodeURIComponent(JSON.stringify(actor))
        ];
        if (registrationId) queryParams.push('registration=' + encodeURIComponent(registrationId));
        if (lmsSubscriptionId) queryParams.push('subscriptionId=' + encodeURIComponent(lmsSubscriptionId));
        if (lmsStudentID) queryParams.push('studentID=' + encodeURIComponent(lmsStudentID));
        if (lmsPortalId) queryParams.push('portalId=' + encodeURIComponent(lmsPortalId));
        if (lmsIdentifier) queryParams.push('identifier=' + encodeURIComponent(lmsIdentifier));
        stateUrl += '?' + queryParams.join('&');
        var xhr = new XMLHttpRequest();
        xhr.open('DELETE', stateUrl, true);
        xhr.setRequestHeader('X-Experience-API-Version', '1.0.3');
        if (xapiAuth) xhr.setRequestHeader('Authorization', xapiAuth);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                console.log('Bookmark deleted from LRS (course completed)');
            }
        };
        xhr.send();
    } catch(e) {
        console.error('Error deleting bookmark from LRS:', e);
    }
}

// Resume from bookmark data (LMS or localStorage)
function resumeFromBookmark(progress) {
    try {
        if (!progress || progress.currentModule <= 0) {
            startCourse();
            return;
        }
        console.log('Resuming from Module ' + progress.currentModule + ', Section ' + (progress.currentSection || 1));
        _isResuming = true;

        // Send xAPI attempted/resumed statement
        if (xapiInitialized && !window.courseStarted) {
            sendStatement(VERBS.attempted, courseURI, document.title, 'Learner resumed the course.', null, null, "http://adlnet.gov/expapi/activities/course");
        }

        // Restore completed modules state
        if (progress.modulesCompleted) {
            for (var key in progress.modulesCompleted) {
                modulesCompleted[key] = progress.modulesCompleted[key];
            }
        }
        if (progress.knowledgeChecksCompleted) {
            for (var key in progress.knowledgeChecksCompleted) {
                knowledgeChecksCompleted[key] = progress.knowledgeChecksCompleted[key];
            }
        }
        if (progress.sectionsCompleted) {
            for (var key in progress.sectionsCompleted) {
                sectionsCompleted[key] = progress.sectionsCompleted[key];
            }
        }
        quizRetryCount = progress.quizRetryCount || 0;

        // Hide home screen
        var homeScreen = document.getElementById('homeScreen');
        if (homeScreen) homeScreen.style.display = 'none';

        // Hide instructions (already seen)
        var instructionsSection = document.getElementById('courseInstructionsSection');
        if (instructionsSection) instructionsSection.style.display = 'none';

        // Show sidebar and main content
        var sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.style.display = 'flex';
            sidebar.classList.add('visible');
        }
        var mainContent = document.getElementById('mainContent');
        if (mainContent) mainContent.style.display = 'block';

        // Set course started flag
        window.courseStarted = true;
        initializeContinueButtonFallback();

        // Restore module/section position
        currentModule = progress.currentModule;
        currentSection = {
            module: progress.currentModule,
            section: progress.currentSection || 1
        };

        // Update sidebar to show completed modules
        for (var modNum in progress.modulesCompleted) {
            if (progress.modulesCompleted[modNum]) {
                var navItem = document.querySelector('.module-nav-item[data-module="' + modNum + '"]');
                if (navItem) {
                    navItem.classList.add('completed');
                    navItem.classList.remove('locked');
                    var completedIcon = navItem.querySelector('.completed-icon');
                    if (completedIcon) completedIcon.style.display = 'inline';
                    var lockedIcon = navItem.querySelector('.locked-icon');
                    if (lockedIcon) lockedIcon.style.display = 'none';
                }
            }
        }

        // Unlock current module nav item
        var currentNavItem = document.querySelector('.module-nav-item[data-module="' + progress.currentModule + '"]');
        if (currentNavItem) {
            currentNavItem.classList.remove('locked');
            var lockedIcon = currentNavItem.querySelector('.locked-icon');
            if (lockedIcon) lockedIcon.style.display = 'none';
        }

        // Navigate to saved module
        showModule(progress.currentModule, true);

        // Show correct section within module
        var targetSectionNum = progress.currentSection || 1;
        if (targetSectionNum > 1) {
            document.querySelectorAll('[id^="module-' + progress.currentModule + '-section-"]').forEach(function(sec) {
                sec.style.display = 'none';
            });
            var targetSection = document.getElementById('module-' + progress.currentModule + '-section-' + targetSectionNum);
            if (targetSection) {
                targetSection.style.display = 'block';
                currentSection.section = targetSectionNum;
            }
        }

        _isResuming = false;
        updateProgress();
        window.scrollTo(0, 0);
        saveCourseProgress();
        console.log('Course resumed at Module ' + progress.currentModule + ', Section ' + targetSectionNum);

    } catch(e) {
        _isResuming = false;
        console.error('Error resuming course:', e);
        startCourse();
    }
}

// Save progress on tab close (last chance)
window.addEventListener('beforeunload', function() {
    if (window.courseStarted && currentModule > 0) {
        saveCourseProgress();
    }
});

// Resume course from saved progress (called internally, not from UI button)
function resumeCourse() {
    var progress = lmsBookmark || getCourseProgress();
    if (!progress || progress.currentModule <= 0) {
        console.log('No saved progress found - starting fresh');
        startCourse();
        return;
    }
    resumeFromBookmark(progress);
}

function showSkipButton() {
    // Skip button functionally removed. Maps to the standard continue flow.
    unlockInstructionsNavigation();
}

function enableInstructionsContinue() {
    var lockMsg = document.getElementById('instructionsLockMsg');
    if (lockMsg) lockMsg.style.display = 'none';
    var continueBtn = document.getElementById('instructionsContinueBtn');
    if (continueBtn) {
        continueBtn.style.display = 'block';
        continueBtn.disabled = false;
    }
}

function completeInstructions() {
    proceedToFirstModule();
}

function unlockInstructionsNavigation() {
    enableInstructionsContinue();
}

function proceedToFirstModule() {
    try {
        // Hide instructions section
        const instructionsSection = document.getElementById('courseInstructionsSection');
        if (instructionsSection) {
            instructionsSection.style.display = 'none';
        }
        
        // Show sidebar
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.style.display = 'flex';
        }
        
        // Show main content area
        const mainContent = document.getElementById('mainContent');
        if (mainContent) {
            mainContent.style.display = 'block';
        }
        
        // Show desktop sidebar toggle
        const desktopToggle = document.querySelector('.desktop-sidebar-toggle');
        if (desktopToggle) {
            desktopToggle.style.display = 'flex';
        }
        
        // Set course started flag - enables audio autoplay
        window.courseStarted = true;
        
        // Initialize global fallback for continue buttons
        initializeContinueButtonFallback();
        
        currentModule = 1;
        currentSection.module = 1;
        currentSection.section = 1;
        
        // First module is always unlocked
        modulesCompleted[0] = true; // Module 0 means ready to start
        
        // Ensure modulesCompleted object exists
        if (!modulesCompleted) {
            modulesCompleted = {};
        }
        modulesCompleted[0] = true;
        
        // Hide all module sections first
        document.querySelectorAll('.module-section').forEach(module => {
            module.style.display = 'none';
        });
        
        // Hide all content sections first (in case any are visible)
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show first section of first module (RISE 365: first lesson fits above fold)
        const firstSection = document.getElementById('module-1-section-1');
        if (firstSection) {
            // Show the parent module-section container
            const firstModule = document.getElementById('module-1');
            if (firstModule) {
                firstModule.style.display = 'block';
            }
            
            // Show the first section
            firstSection.style.display = 'block';
            window.scrollTo(0, 0);
            
            // Stop all other audios first
            document.querySelectorAll('audio').forEach(audio => {
                if (!audio.paused) {
                    audio.pause();
                    audio.currentTime = 0;
                }
            });
            
            // Trigger audio autoplay for first section after a short delay
            setTimeout(() => {
                const firstAudio = firstSection.querySelector('audio');
                if (firstAudio) {
                    // For chunked audio, trigger loadNextChunk
                    if (firstAudio.hasAttribute('data-chunked')) {
                        // Try different function name patterns
                        const loadNextFunc1 = window['loadNextChunk_1_1'];
                        const loadNextFunc2 = window['loadNextChunk_1'];
                        if (typeof loadNextFunc1 === 'function') {
                            loadNextFunc1();
                        } else if (typeof loadNextFunc2 === 'function') {
                            loadNextFunc2();
                        }
                    }
                    // Try to play audio
                    firstAudio.play().catch(e => console.log('Autoplay prevented:', e));
                }
            }, 500);
        } else {
            console.error('First section not found: module-1-section-1');
            // Fallback to module-level navigation
            const firstModule = document.getElementById('module-1');
            if (firstModule) {
                firstModule.style.display = 'block';
            }
        }
        
        updateProgress();
    } catch (error) {
        console.error('Error in proceedToFirstModule:', error);
        alert(window.uiLabels.error_refresh);
    }
}

function navigateToModule(moduleNum) {
    // Navigate to the last visited section in this module, or section 1 if first visit.
    // navigateToSection handles module-lock checks, display logic, and tracking.
    const targetSection = lastModuleSection[moduleNum] || 1;
    navigateToSection(moduleNum, targetSection);
}

// Navigate to a specific section within a module (triggered from sidebar section nav)
function navigateToSection(moduleNum, sectionNum) {
    // First navigate to the module
    if (moduleNum > 1 && !modulesCompleted[moduleNum - 1] && !modulesCompleted[moduleNum]) {
        alert(window.uiLabels.complete_prev_module);
        return;
    }
    
    // Only allow navigating to completed sections or the current section
    const sectionKey = `${moduleNum}.${sectionNum}`;
    const prevSectionKey = sectionNum > 1 ? `${moduleNum}.${sectionNum - 1}` : null;
    const isFirstSection = sectionNum === 1;
    const isPrevCompleted = prevSectionKey ? sectionsCompleted[prevSectionKey] : true;
    const isSectionCompleted = sectionsCompleted[sectionKey];
    const isCurrentSection = currentSection.module === moduleNum && currentSection.section === sectionNum;
    
    if (!isFirstSection && !isPrevCompleted && !isSectionCompleted && !isCurrentSection) {
        return; // Section is locked
    }
    
    // Auto-expand the module's accordion
    collapseAllModules();
    const content = document.getElementById('accordion-content-' + moduleNum);
    const chevron = document.querySelector('.chevron-icon-' + moduleNum);
    if (content) content.style.display = 'block';
    if (chevron) chevron.style.transform = 'rotate(180deg)';
    
    // Hide all modules
    document.querySelectorAll('.module-section').forEach(m => {
        m.style.display = 'none';
    });

    // Hide quiz and completion sections
    ['quizSection', 'quizIntroSection', 'quizResultsSection', 'completionSection'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    // Show the target module
    const moduleEl = document.getElementById('module-' + moduleNum);
    if (moduleEl) moduleEl.style.display = 'block';
    
    // Hide all sections within this module
    document.querySelectorAll(`[id^="module-${moduleNum}-section-"]`).forEach(s => {
        s.style.display = 'none';
    });
    
    // Show the target section
    const sectionEl = document.getElementById(`module-${moduleNum}-section-${sectionNum}`);
    if (sectionEl) {
        sectionEl.style.display = 'block';
        window.scrollTo(0, 0);
    }
    
    // Update tracking
    currentModule = moduleNum;
    currentSection = { module: moduleNum, section: sectionNum };
    lastModuleSection[moduleNum] = sectionNum;
    updateProgress();
}

function showQuizNavItem() {
    const quizNavItem = document.getElementById('quiz-nav-item');
    if (quizNavItem) quizNavItem.style.display = 'flex';
}

function navigateToQuiz() {
    // Hide all modules and their sections
    document.querySelectorAll('.module-section').forEach(m => {
        m.style.display = 'none';
    });
    document.querySelectorAll('.content-section').forEach(s => {
        s.style.display = 'none';
    });
    // Hide completion section
    const completionSection = document.getElementById('completionSection');
    if (completionSection) completionSection.style.display = 'none';

    // Resume from where the learner left off
    if (quizState === 'active') {
        const el = document.getElementById('quizSection');
        if (el) { el.style.display = 'block'; window.scrollTo(0, 0); }
    } else if (quizState === 'results') {
        const el = document.getElementById('quizResultsSection');
        if (el) { el.style.display = 'block'; window.scrollTo(0, 0); }
    } else {
        // 'intro' or not yet started
        const el = document.getElementById('quizIntroSection');
        if (el) { el.style.display = 'block'; window.scrollTo(0, 0); }
    }
}

function toggleAllModules() {
    const expandAll = !document.querySelector('.module-accordion-content[style*="display: block"]');
    
    document.querySelectorAll('.module-accordion-content').forEach(content => {
        content.style.display = expandAll ? 'block' : 'none';
    });
    
    document.querySelectorAll('[class^="chevron-icon-"]').forEach(chevron => {
        chevron.style.transform = expandAll ? 'rotate(180deg)' : 'rotate(0deg)';
    });

    const btn = document.getElementById('toggleAllBtn');
    if (btn) {
        if (expandAll) {
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg> Collapse All';
        } else {
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg> Expand All';
        }
    }
}

function collapseAllModules() {
    // Legacy function support - redirect to toggle logic to close all
    document.querySelectorAll('.module-accordion-content').forEach(content => {
        content.style.display = 'none';
    });
    document.querySelectorAll('[class^="chevron-icon-"]').forEach(chevron => {
        chevron.style.transform = 'rotate(0deg)';
    });
    const btn = document.getElementById('toggleAllBtn');
    if (btn) {
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg> Expand All';
    }
}

function toggleModuleAccordion(moduleNum, event) {
    if (event) {
        event.stopPropagation();
    }
    const content = document.getElementById('accordion-content-' + moduleNum);
    const chevron = document.querySelector('.chevron-icon-' + moduleNum);
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        if (chevron) chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        if (chevron) chevron.style.transform = 'rotate(0deg)';
    }
}

function toggleDesktopSidebar() {
    const container = document.querySelector('.course-container');
    if (container) {
        container.classList.toggle('sidebar-closed');
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function showModule(moduleNum, isRevisit = false) {
    try {
        // Allow revisiting completed modules - only block if module is locked (not completed yet)
        if (!isRevisit && moduleNum > 1 && !modulesCompleted[moduleNum - 1] && !modulesCompleted[moduleNum]) {
            alert(window.uiLabels.complete_prev_module);
            return;
        }
        
        // Stop all currently playing audio to prevent overlap
        document.querySelectorAll('audio').forEach(audio => {
            if (!audio.paused) {
                audio.pause();
                audio.currentTime = 0;
            }
        });
        
        // Reset any chunked audio to start from beginning
        const resetFunc = window['resetAudio_' + moduleNum];
        if (typeof resetFunc === 'function') {
            resetFunc();
        }
        
        // Only reset completion tracking if this is not a revisit
        if (!isRevisit) {
            if (!audioPlayed) audioPlayed = {};
            if (!contentScrolled) contentScrolled = {};
            if (!moduleCompletionStatus) moduleCompletionStatus = {};
            
            audioPlayed[moduleNum] = false;
            contentScrolled[moduleNum] = false;
            moduleCompletionStatus[moduleNum] = {
                audioFinished: false,
                contentViewed: false,
                knowledgeCheckPassed: false
            };
        }

        // Ensure module tracking exists even for revisit navigation (covers modules not visited yet)
        if (!moduleCompletionStatus) moduleCompletionStatus = {};
        if (!audioPlayed) audioPlayed = {};
        if (!contentScrolled) contentScrolled = {};
        if (!moduleCompletionStatus[moduleNum]) {
            moduleCompletionStatus[moduleNum] = {
                audioFinished: false,
                contentViewed: false,
                knowledgeCheckPassed: false
            };
        }
        if (typeof audioPlayed[moduleNum] === 'undefined') audioPlayed[moduleNum] = false;
        if (typeof contentScrolled[moduleNum] === 'undefined') contentScrolled[moduleNum] = false;
        
        // Hide ALL modules first (only show current one)
        document.querySelectorAll('.module-section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Hide quiz and completion sections
        const quizSection = document.getElementById('quizSection');
        if (quizSection) quizSection.style.display = 'none';
        const quizIntroSection = document.getElementById('quizIntroSection');
        if (quizIntroSection) quizIntroSection.style.display = 'none';
        const quizResultsSection = document.getElementById('quizResultsSection');
        if (quizResultsSection) quizResultsSection.style.display = 'none';
        const completionSection = document.getElementById('completionSection');
        if (completionSection) completionSection.style.display = 'none';
        
        const moduleElement = document.getElementById('module-' + moduleNum);
        if (moduleElement) {
            // Show only the current module
            moduleElement.style.display = 'block';
            

            
            // Hide ALL content-section divs inside this module first
            moduleElement.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            
            // Show only the first section of this module
            const firstSection = document.getElementById(`module-${moduleNum}-section-1`);
            if (firstSection) {
                firstSection.style.display = 'block';
            }
            
            window.scrollTo(0, 0); // Scroll to top of module
            
            // Update current section tracking
            currentModule = moduleNum;
            currentSection.module = moduleNum;
            currentSection.section = 1;

            // Ensure knowledge check visibility
            const kcContainer = document.getElementById('kc-' + moduleNum);
            const kcLockMessage = document.getElementById('kc-lock-message-' + moduleNum);
            if (kcContainer) {
                // If revisiting a completed module, always show KC unlocked
                const isModuleCompleted = modulesCompleted[moduleNum];
                const audioFinished = moduleCompletionStatus[moduleNum] && moduleCompletionStatus[moduleNum].audioFinished;
                
                if (isModuleCompleted || audioFinished) {
                    kcContainer.style.display = 'block';
                    if (kcLockMessage) kcLockMessage.style.display = 'none';
                    kcContainer.querySelectorAll('.kc-option-btn').forEach(b => b.disabled = false);
                } else {
                    kcContainer.style.display = 'block';
                    if (kcLockMessage) kcLockMessage.style.display = 'flex';
                    kcContainer.querySelectorAll('.kc-option-btn').forEach(b => b.disabled = true);
                }
            }

            // Update sidebar active state
            document.querySelectorAll('.module-nav-item').forEach(item => {
                const itemModuleNum = parseInt(item.getAttribute('data-module'));
                const circle = item.querySelector('.module-nav-circle');
                
                if (itemModuleNum === moduleNum) {
                    item.classList.add('active');
                    item.classList.remove('completed', 'locked'); // Remove completed/locked class when active
                    if (circle) {
                        circle.style.background = '#025e9b';
                        circle.style.borderColor = '#025e9b';
                        circle.style.boxShadow = '0 0 0 2px rgba(2, 94, 155, 0.2)';
                    }
                    // Hide status icons when active
                    const completedIcon = item.querySelector('.completed-icon');
                    const lockedIcon = item.querySelector('.locked-icon');
                    if (completedIcon) completedIcon.style.display = 'none';
                    if (lockedIcon) lockedIcon.style.display = 'none';
                } else {
                    item.classList.remove('active');
                    if (circle) {
                        // Reset circle to default state
                        circle.style.background = 'transparent';
                        circle.style.borderColor = '#ccc';
                        circle.style.boxShadow = 'none';
                    }
                    
                    // Show completed icon if module is completed
                    if (modulesCompleted[itemModuleNum]) {
                        item.classList.add('completed');
                        item.classList.remove('locked');
                        const completedIcon = item.querySelector('.completed-icon');
                        if (completedIcon) completedIcon.style.display = 'inline';
                        const lockedIcon = item.querySelector('.locked-icon');
                        if (lockedIcon) lockedIcon.style.display = 'none';
                        if (circle) {
                            circle.style.borderColor = '#999';
                        }
                    } else if (itemModuleNum > 1 && !modulesCompleted[itemModuleNum - 1]) {
                        // Module is locked
                        item.classList.add('locked');
                        item.classList.remove('completed');
                        const lockedIcon = item.querySelector('.locked-icon');
                        if (lockedIcon) lockedIcon.style.display = 'inline';
                        const completedIcon = item.querySelector('.completed-icon');
                        if (completedIcon) completedIcon.style.display = 'none';
                        if (circle) {
                            circle.style.borderColor = '#ccc';
                            circle.style.background = '#f5f5f5';
                            circle.style.opacity = '0.5';
                        }
                    }
                }
            });
            
            // Lock Continue button until module is completed
            const continueButton = document.getElementById('continue-' + moduleNum);
            if (continueButton) {
                continueButton.disabled = true;
                continueButton.textContent = window.uiLabels.continue_btn || 'Continue';
            }
        
        // Track scrolling to detect when user has viewed content
        let scrollTimeout;
        const moduleContent = moduleElement.querySelector('.module-content');
        if (moduleContent) {
            const checkScroll = () => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                const windowHeight = window.innerHeight;
                const documentHeight = document.documentElement.scrollHeight;
                
                // Consider content viewed if user has scrolled through most of it
                if (scrollTop + windowHeight >= documentHeight - 100) {
                    contentScrolled[moduleNum] = true;
                    moduleCompletionStatus[moduleNum].contentViewed = true;
                    checkModuleCompletion(moduleNum);
                }
            };
            
            window.addEventListener('scroll', () => {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(checkScroll, 500);
            });
            
            // Also check on initial load if content is short
            setTimeout(checkScroll, 1000);
        }
        
        // Update progress
        updateProgress();
        if (!_isResuming) saveCourseProgress();
        
        // Play audio for this module only after all others are stopped
        const audio = moduleElement.querySelector('audio');
        if (audio) {
            audio.currentTime = 0; // Reset audio to beginning
            
            // Track audio completion
            const trackAudioCompletion = () => {
                audioPlayed[moduleNum] = true;
                moduleCompletionStatus[moduleNum].audioFinished = true;
                checkModuleCompletion(moduleNum);
            };
            
            // Listen for audio end
            audio.addEventListener('ended', trackAudioCompletion, { once: true });
            
            // For chunked audio, track when all chunks are done
            if (audio.hasAttribute('data-chunked')) {
                const loadNextChunkFunc = window['loadNextChunk_' + moduleNum];
                if (typeof loadNextChunkFunc === 'function') {
                    // Track chunk completion
                    let chunkIndex = 0;
                    const totalChunks = parseInt(audio.getAttribute('data-total-chunks') || '1');
                    
                    // Override the loadNextChunk function to track completion
                    const originalFunc = loadNextChunkFunc;
                    window['loadNextChunk_' + moduleNum] = function() {
                        originalFunc();
                        chunkIndex++;
                        if (chunkIndex >= totalChunks) {
                            trackAudioCompletion();
                        }
                    };
                    
                    setTimeout(() => { loadNextChunkFunc(); }, 300);
                } else {
                    setTimeout(() => { audio.play().catch(e => console.log('Autoplay prevented:', e)); }, 300);
                }
            } else {
                setTimeout(() => { audio.play().catch(e => console.log('Autoplay prevented:', e)); }, 300);
            }
        } else {
            // No audio for this module, mark as complete
            audioPlayed[moduleNum] = true;
            moduleCompletionStatus[moduleNum].audioFinished = true;
            checkModuleCompletion(moduleNum);
        }
        // Update progress
        updateProgress();
    } else {
        console.error('Module element not found: module-' + moduleNum);
        // Try to show first available module as fallback
        const firstModule = document.querySelector('.module-section');
        if (firstModule) {
            firstModule.style.display = 'block';
            console.log('Showed first available module as fallback');
        } else {
            console.error('No modules found in DOM');
            alert(window.uiLabels.no_modules_found);
        }
    }
    } catch (error) {
        console.error('Error in showModule:', error);
        alert(window.uiLabels.error_refresh);
    }
}

function checkModuleCompletion(moduleNum) {
    const status = moduleCompletionStatus[moduleNum];
    if (!status) return;
    
    const moduleData = window.courseData?.modules?.[moduleNum - 1];
    const hasKnowledgeCheck = moduleData?.knowledgeCheck;
    
    // Check if all requirements are met
    const audioComplete = status.audioFinished;
    const contentComplete = status.contentViewed;
    const knowledgeCheckComplete = !hasKnowledgeCheck || status.knowledgeCheckPassed;
    
    const allComplete = audioComplete && contentComplete && knowledgeCheckComplete;
    
    // Enable Continue button if all requirements met
    const continueButton = document.getElementById('continue-' + moduleNum);
    if (continueButton && allComplete) {
        continueButton.disabled = false;
    }
}

function markModuleCompleted(moduleNum) {
    modulesCompleted[moduleNum] = true;
    
    // Update sidebar - unlock next module
    const nextModuleNum = moduleNum + 1;
    if (nextModuleNum <= totalModules) {
        const nextNavItem = document.querySelector(`.module-nav-item[data-module="${nextModuleNum}"]`);
        if (nextNavItem) {
            nextNavItem.classList.remove('locked');
            nextNavItem.onclick = function() { navigateToModule(nextModuleNum); };
            const lockedIcon = nextNavItem.querySelector('.locked-icon');
            if (lockedIcon) lockedIcon.style.display = 'none';
            const circle = nextNavItem.querySelector('.module-nav-circle');
            if (circle) {
                circle.style.opacity = '1';
                circle.style.background = 'transparent';
            }
        }
    }
    
    // Update current module status in sidebar - make it clickable for revisiting
    const currentNavItem = document.querySelector(`.module-nav-item[data-module="${moduleNum}"]`);
    if (currentNavItem) {
        const completedIcon = currentNavItem.querySelector('.completed-icon');
        if (completedIcon) completedIcon.style.display = 'inline';
        // Remove active class but keep it clickable
        currentNavItem.classList.remove('active');
        currentNavItem.classList.add('completed');
        // Update circle to show completed state
        const circle = currentNavItem.querySelector('.module-nav-circle');
        if (circle) {
            circle.style.background = 'transparent';
            circle.style.borderColor = '#999';
            circle.style.boxShadow = 'none';
        }
        // Ensure it's still clickable for revisiting
        if (!currentNavItem.onclick || currentNavItem.onclick.toString().indexOf('navigateToModule') === -1) {
            currentNavItem.onclick = function() { navigateToModule(moduleNum); };
        }
        // Add cursor pointer style
        currentNavItem.style.cursor = 'pointer';
    }
    
    console.log(`✅ Module ${moduleNum} marked as completed - can be revisited via sidebar`);
}

// Unlock all modules (called when course is completed)
function unlockAllModules() {
    for (let i = 1; i <= totalModules; i++) {
        modulesCompleted[i] = true;
        const navItem = document.querySelector(`.module-nav-item[data-module="${i}"]`);
        if (navItem) {
            navItem.classList.remove('locked');
            navItem.classList.add('completed');
            navItem.onclick = function() { navigateToModule(i); };
            navItem.style.cursor = 'pointer';
            const lockedIcon = navItem.querySelector('.locked-icon');
            if (lockedIcon) lockedIcon.style.display = 'none';
            
            // Mark as completed
            const completedIcon = navItem.querySelector('.completed-icon');
            if (completedIcon) {
                completedIcon.style.display = 'inline';
            }
        }
    }
    console.log('✅ All modules unlocked - course completed! All modules can be revisited.');
}

// Section-level navigation (RISE 365: Continue button after each section)
// Note: currentSection and sectionsCompleted are already declared above

function continueToNextSection(moduleNum, sectionNum, totalSections) {
    try {
        // Mark current section as completed
        const sectionKey = `${moduleNum}.${sectionNum}`;
        sectionsCompleted[sectionKey] = true;
        
        // Send xAPI experienced statement for the completed section (Rise360 compatible)
        if (xapiInitialized) {
            const moduleData = window.courseData?.modules?.[moduleNum - 1];
            const sectionData = moduleData?.content?.sections?.[sectionNum - 1];
            const sectionTitle = sectionData?.sectionTitle || `Section ${sectionNum}`;
            const sectionID = courseURI + "/module/" + moduleNum + "/section/" + sectionNum;
            sendStatement(VERBS.experienced, sectionID, sectionTitle, 
                "Learner completed section " + sectionNum + " of module " + moduleNum, 
                null, null, "http://adlnet.gov/expapi/activities/module");
        }
        
        // Hide current section
        const currentSectionId = `module-${moduleNum}-section-${sectionNum}`;
        const currentSectionEl = document.getElementById(currentSectionId);
        if (currentSectionEl) {
            currentSectionEl.style.display = 'none';
        }
        
        // Check if this is the last section in the module
        if (sectionNum < totalSections) {
                // Show next section in same module
                const nextSectionId = `module-${moduleNum}-section-${sectionNum + 1}`;
                const nextSection = document.getElementById(nextSectionId);
                if (nextSection) {
                    // Ensure parent module-section is visible
                    const parentModule = document.getElementById('module-' + moduleNum);
                    
                    // Trigger completion check for the newly shown section after a short delay
                    setTimeout(() => {
                        const nextSectionNum = sectionNum + 1;
                        const checkFunc = window['checkSectionCompletion_' + moduleNum + '_' + nextSectionNum];
                        if (typeof checkFunc === 'function') {
                            checkFunc();
                        }
                    }, 300);
                    if (parentModule) {
                        parentModule.style.display = 'block';
                    }
                    
                    nextSection.style.display = 'block';
                    window.scrollTo(0, 0); // Scroll to top
                
                // Update current section tracking
                currentSection.module = moduleNum;
                currentSection.section = sectionNum + 1;
                lastModuleSection[moduleNum] = sectionNum + 1;

                // Trigger audio autoplay IMMEDIATELY (no delay)
                const nextSectionAudioId = `audio-${moduleNum}-${sectionNum + 1}`;
                const autoplayKey = `section_${moduleNum}_${sectionNum + 1}_audio_autoplayed`;
                const trackingKey = `section_${moduleNum}_${sectionNum + 1}_tracking`;
                
                // Function to play audio
                const playAudio = () => {
                    const nextSectionAudio = document.getElementById(nextSectionAudioId);
                    
                    if (!nextSectionAudio) {
                        console.warn(`Audio element not found: ${nextSectionAudioId}, checking for chunked audio...`);
                        // Check if this is chunked audio that needs loadNextChunk function
                        const loadNextChunkFunc = window['loadNextChunk_' + moduleNum + '_' + (sectionNum + 1)];
                        if (typeof loadNextChunkFunc === 'function') {
                            // Chunked audio - trigger loadNextChunk
                            setTimeout(() => {
                                // Stop all other audio first
                                document.querySelectorAll('audio').forEach(otherAudio => {
                                    if (!otherAudio.paused) {
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }
                                });
                                loadNextChunkFunc();
                                window[autoplayKey] = true;
                                if (window[trackingKey]) {
                                    window[trackingKey].audioPlayed = true;
                                }
                                console.log(`✅ Chunked audio autoplay triggered for section ${moduleNum}.${sectionNum + 1}`);
                            }, 100);
                            return true;
                        }
                        // No audio for this section - that's okay
                        console.log(`No audio element found for section ${moduleNum}.${sectionNum + 1} - continuing without audio`);
                        return true;
                    }
                    
                    if (!window.courseStarted) {
                        console.warn('Course not started yet');
                        return false;
                    }
                    
                    if (window[autoplayKey]) {
                        console.log(`Audio already autoplayed for section ${moduleNum}.${sectionNum + 1}`);
                        return true; // Already played
                    }
                    
                    // Check if this is chunked audio
                    if (nextSectionAudio.hasAttribute('data-chunked')) {
                        const loadNextChunkFunc = window['loadNextChunk_' + moduleNum + '_' + (sectionNum + 1)];
                        if (typeof loadNextChunkFunc === 'function') {
                            // Stop all other audio first
                            document.querySelectorAll('audio').forEach(otherAudio => {
                                if (otherAudio !== nextSectionAudio && !otherAudio.paused) {
                                    otherAudio.pause();
                                    otherAudio.currentTime = 0;
                                }
                            });
                            setTimeout(() => {
                                loadNextChunkFunc();
                                window[autoplayKey] = true;
                                if (window[trackingKey]) {
                                    window[trackingKey].audioPlayed = true;
                                }
                                console.log(`✅ Chunked audio autoplay triggered for section ${moduleNum}.${sectionNum + 1}`);
                            }, 100);
                            return true;
                        }
                    }
                    
                    // Stop all other audio first
                    document.querySelectorAll('audio').forEach(otherAudio => {
                        if (otherAudio !== nextSectionAudio && !otherAudio.paused) {
                            otherAudio.pause();
                            otherAudio.currentTime = 0;
                        }
                    });
                    
                    // Force play immediately
                    const playPromise = nextSectionAudio.play();
                    if (playPromise !== undefined) {
                        playPromise.then(() => {
                            window[autoplayKey] = true;
                            
                            // Mark audio as played in tracking
                            if (window[trackingKey]) {
                                window[trackingKey].audioPlayed = true;
                            }
                            
                            console.log(`✅ Audio autoplay triggered IMMEDIATELY for section ${moduleNum}.${sectionNum + 1}`);
                            
                            // Set up ended listener to mark as completed
                            nextSectionAudio.addEventListener('ended', function() {
                                if (window[trackingKey]) {
                                    window[trackingKey].audioCompleted = true;
                                    const checkFunc = window['checkSectionCompletion_' + moduleNum + '_' + (sectionNum + 1)];
                                    if (typeof checkFunc === 'function') {
                                        checkFunc();
                                    }
                                }
                            }, { once: true });
                        }).catch(e => {
                            console.log('Autoplay prevented for next section, will retry:', e);
                            // Retry after a short delay if autoplay was prevented
                            setTimeout(() => {
                                const retryAudio = document.getElementById(nextSectionAudioId);
                                if (retryAudio) {
                                    retryAudio.play().catch(err => {
                                        console.log('Retry autoplay failed:', err);
                                    });
                                }
                            }, 300);
                        });
                    }
                    return true;
                };
                
                // Try immediately
                if (!playAudio()) {
                    // If failed, retry after short delays
                    setTimeout(() => playAudio(), 50);
                    setTimeout(() => playAudio(), 200);
                }
            } else {
                console.error('Next section not found:', nextSectionId);
            }
        } else {
            // Last section in module - mark module as completed
            markModuleCompleted(moduleNum);
            
            // Hide the completed module completely (only show current module)
            const completedModule = document.getElementById('module-' + moduleNum);
            if (completedModule) {
                completedModule.style.display = 'none';
            }
            
            // Check if there are more modules
            const totalModules = window.courseData?.modules?.length || 0;
            
            if (moduleNum < totalModules) {
                // Move to first section of next module
                const nextModuleFirstSectionId = `module-${moduleNum + 1}-section-1`;
                const nextModuleFirstSection = document.getElementById(nextModuleFirstSectionId);
                
                // Hide all other modules first
                document.querySelectorAll('.module-section').forEach(moduleEl => {
                    moduleEl.style.display = 'none';
                });
                
                if (nextModuleFirstSection) {
                    // Ensure parent module-section is visible
                    const parentModule = document.getElementById('module-' + (moduleNum + 1));
                    if (parentModule) {
                        // Hide ALL sections in next module first (prevents lingering display:block from a prior visit)
                        parentModule.querySelectorAll('.content-section').forEach(s => {
                            s.style.display = 'none';
                        });
                        parentModule.style.display = 'block';
                    }

                    nextModuleFirstSection.style.display = 'block';
                    window.scrollTo(0, 0);
                    
                    // Update tracking
                    currentModule = moduleNum + 1;
                    currentSection.module = moduleNum + 1;
                    currentSection.section = 1;
                    lastModuleSection[moduleNum + 1] = 1;
                    
                    // Trigger audio autoplay IMMEDIATELY (no delay)
                    const nextModuleFirstAudioId = `audio-${moduleNum + 1}-1`;
                    const autoplayKey = `section_${moduleNum + 1}_1_audio_autoplayed`;
                    const trackingKey = `section_${moduleNum + 1}_1_tracking`;
                    
                    // Function to play audio
                    const playAudio = () => {
                        const nextModuleFirstAudio = document.getElementById(nextModuleFirstAudioId);
                        
                        if (!nextModuleFirstAudio) {
                            console.warn(`Audio element not found: ${nextModuleFirstAudioId}, checking for chunked audio...`);
                            // Check if this is chunked audio that needs loadNextChunk function
                            const loadNextChunkFunc = window['loadNextChunk_' + (moduleNum + 1) + '_1'];
                            if (typeof loadNextChunkFunc === 'function') {
                                // Chunked audio - trigger loadNextChunk
                                setTimeout(() => {
                                    loadNextChunkFunc();
                                    window[autoplayKey] = true;
                                    if (window[trackingKey]) {
                                        window[trackingKey].audioPlayed = true;
                                    }
                                    console.log(`✅ Chunked audio autoplay triggered for module ${moduleNum + 1}, section 1`);
                                }, 100);
                                return true;
                            }
                            // No audio for this section - that's okay
                            console.log(`No audio element found for module ${moduleNum + 1}, section 1 - continuing without audio`);
                            return true;
                        }
                        
                        if (!window.courseStarted) {
                            console.warn('Course not started yet');
                            return false;
                        }
                        
                        if (window[autoplayKey]) {
                            console.log(`Audio already autoplayed for module ${moduleNum + 1}, section 1`);
                            return true; // Already played
                        }
                        
                        // Check if this is chunked audio
                        if (nextModuleFirstAudio.hasAttribute('data-chunked')) {
                            const loadNextChunkFunc = window['loadNextChunk_' + (moduleNum + 1) + '_1'];
                            if (typeof loadNextChunkFunc === 'function') {
                                // Stop all other audio first
                                document.querySelectorAll('audio').forEach(otherAudio => {
                                    if (otherAudio !== nextModuleFirstAudio && !otherAudio.paused) {
                                        otherAudio.pause();
                                        otherAudio.currentTime = 0;
                                    }
                                });
                                setTimeout(() => {
                                    loadNextChunkFunc();
                                    window[autoplayKey] = true;
                                    if (window[trackingKey]) {
                                        window[trackingKey].audioPlayed = true;
                                    }
                                    console.log(`✅ Chunked audio autoplay triggered for module ${moduleNum + 1}, section 1`);
                                }, 100);
                                return true;
                            }
                        }
                        
                        // Stop all other audio first
                        document.querySelectorAll('audio').forEach(otherAudio => {
                            if (otherAudio !== nextModuleFirstAudio && !otherAudio.paused) {
                                otherAudio.pause();
                                otherAudio.currentTime = 0;
                            }
                        });
                        
                        // Force play immediately
                        const playPromise = nextModuleFirstAudio.play();
                        if (playPromise !== undefined) {
                            playPromise.then(() => {
                                window[autoplayKey] = true;
                                
                                // Mark audio as played in tracking
                                if (window[trackingKey]) {
                                    window[trackingKey].audioPlayed = true;
                                }
                                
                                console.log(`✅ Audio autoplay triggered IMMEDIATELY for module ${moduleNum + 1}, section 1`);
                                
                                // Set up ended listener to mark as completed
                                nextModuleFirstAudio.addEventListener('ended', function() {
                                    if (window[trackingKey]) {
                                        window[trackingKey].audioCompleted = true;
                                        const checkFunc = window['checkSectionCompletion_' + (moduleNum + 1) + '_1'];
                                        if (typeof checkFunc === 'function') {
                                            checkFunc();
                                        }
                                    }
                                }, { once: true });
                            }).catch(e => {
                                console.log('Autoplay prevented for next module, will retry:', e);
                                // Retry after a short delay if autoplay was prevented
                                setTimeout(() => {
                                    const retryAudio = document.getElementById(nextModuleFirstAudioId);
                                    if (retryAudio) {
                                        retryAudio.play().catch(err => {
                                            console.log('Retry autoplay failed:', err);
                                        });
                                    }
                                }, 300);
                            });
                        }
                        return true;
                    };
                    
                    // Try immediately
                    if (!playAudio()) {
                        // If failed, retry after short delays
                        setTimeout(() => playAudio(), 50);
                        setTimeout(() => playAudio(), 200);
                    }
                } else {
                    console.error('First section of next module not found:', nextModuleFirstSectionId);
                }
            } else {
                // All sections completed - show quiz intro
                document.querySelectorAll('.content-section').forEach(section => {
                    section.style.display = 'none';
                });
                
                // Also hide all module sections
                document.querySelectorAll('.module-section').forEach(moduleEl => {
                    moduleEl.style.display = 'none';
                });
                
                const quizIntro = document.getElementById('quizIntroSection');
                if (quizIntro) {
                    quizIntro.style.display = 'block';
                    quizState = 'intro';
                    showQuizNavItem();
                    window.scrollTo(0, 0);
                    console.log('Quiz intro section displayed');
                } else {
                    // No quiz available - show completion section directly
                    console.log('No quiz section found - showing completion');
                    const completionSection = document.getElementById('completionSection');
                    if (completionSection) {
                        completionSection.style.display = 'block';
                        window.scrollTo(0, 0);
                        trackCourseCompletion();
                    }
                }
            }
        }
        
        updateProgress();
        saveCourseProgress();
    } catch (error) {
        console.error('Error in continueToNextSection:', error);
        alert(window.uiLabels.error_refresh);
    }
}

function continueToNext() {
    // Legacy function - now uses section-level navigation
    if (currentSection.module > 0 && currentSection.section > 0) {
        const moduleData = window.courseData?.modules?.[currentSection.module - 1];
        const sections = moduleData?.content?.sections || [];
        continueToNextSection(currentSection.module, currentSection.section, sections.length);
    }
}

function nextModule() {
    // Alias for continueToNext for backward compatibility
    continueToNext();
}

function previousModule() {
    if (currentModule > 1) {
        currentModule--;
        showModule(currentModule);
    }
}

// Called when a KC radio option is selected - show Submit button
// Called when a KC option card is clicked
function selectKCOption(moduleNum, key) {
    // Disable all options during evaluation
    const buttons = document.querySelectorAll(`#kc-${moduleNum} .kc-option-btn`);
    buttons.forEach(btn => btn.disabled = true);
    
    // Mark selected button
    const selectedBtn = document.getElementById(`kc-${moduleNum}-${key}`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
    }
    
    checkKnowledgeCheck(moduleNum, key);
}

function checkKnowledgeCheck(moduleNum, selectedAnswer) {
    const knowledgeCheck = window.courseData?.modules?.[moduleNum - 1]?.knowledgeCheck;
    if (!knowledgeCheck) return;
    
    const feedbackDiv = document.getElementById('kc-feedback-' + moduleNum);
    
    const isCorrect = selectedAnswer && selectedAnswer.toUpperCase() === (knowledgeCheck.correctAnswer || "").toUpperCase();
    
    if (isCorrect) {
        feedbackDiv.className = 'feedback correct';
        feedbackDiv.innerHTML = '<div style="display: flex; align-items: start; gap: 8px;">' +
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #2e7d32; flex-shrink: 0; margin-top: 2px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>' +
            '<div><strong>' + (window.uiLabels.correct || 'Correct!') + '</strong><br/>' + knowledgeCheck.feedback.correct + '</div></div>';
        
        // Add correct class to selected button
        const selectedBtn = document.getElementById(`kc-${moduleNum}-${selectedAnswer}`);
        if (selectedBtn) {
            selectedBtn.classList.add('correct');
        }
        
        // Find the section that contains this knowledge check and trigger its completion checker
        const kcContainer = document.getElementById('kc-' + moduleNum);
        if (kcContainer) {
            // Find the parent section (knowledge check is in a section-specific container)
            let sectionElement = kcContainer.closest('.content-section');
            if (!sectionElement) {
                // Try finding by section-specific KC container ID
                const sectionKCContainer = kcContainer.closest('[id^="section-' + moduleNum + '-"]');
                if (sectionKCContainer) {
                    sectionElement = sectionKCContainer.closest('.content-section');
                }
            }
            
            if (sectionElement) {
                const sectionId = sectionElement.id;
                // Extract section number from ID (format: module-X-section-Y)
                const match = sectionId.match(/module-(\\d+)-section-(\\d+)/);
                if (match) {
                    const modNum = match[1];
                    const secNum = match[2];
                    const trackingKey = 'section_' + modNum + '_' + secNum + '_tracking';
                    const funcName = 'checkSectionCompletion_' + modNum + '_' + secNum;
                    
                    // Mark KC as completed
                    if (window[trackingKey]) {
                        window[trackingKey].kcCompleted = true;
                    }
                    
                    // Trigger section completion check
                    if (typeof window[funcName] === 'function') {
                        window[funcName]();
                    }
                }
            }
        }
        knowledgeChecksCompleted[moduleNum] = true;
        
        // Mark knowledge check as passed
        if (!moduleCompletionStatus[moduleNum]) {
            moduleCompletionStatus[moduleNum] = {};
        }
        moduleCompletionStatus[moduleNum].knowledgeCheckPassed = true;
        
        // Get total sections to check if this is the last section
        const moduleData = window.courseData?.modules?.[moduleNum - 1];
        const contentData = moduleData?.content;
        const sections = contentData?.sections || [];
        const totalSections = sections.length;
        
        // Check section completion for the last section (where KC is located)
        // This will enable the Continue button
        if (totalSections > 0) {
            checkSectionCompletion(moduleNum, totalSections);
        }
        
        // Check if module can be completed now
        checkModuleCompletion(moduleNum);
    } else {
        feedbackDiv.className = 'feedback incorrect';
        // Use per-option feedback if available (e.g. feedback.B), fall back to generic incorrect
        const optionFeedback = knowledgeCheck.feedback?.[selectedAnswer] || knowledgeCheck.feedback?.incorrect || 'This answer is incorrect. Please select another option.';
        feedbackDiv.innerHTML = '<div style="display: flex; align-items: start; gap: 8px;">' +
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #d32f2f; flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>' +
            '<div><strong>' + (window.uiLabels.try_again || 'Try Again') + '</strong><br/>' + optionFeedback + '</div></div>';
        
        // Add incorrect class to selected button
        const selectedBtn = document.getElementById(`kc-${moduleNum}-${selectedAnswer}`);
        if (selectedBtn) {
            selectedBtn.classList.add('incorrect');
        }
        
        // Re-enable buttons for retry
        const buttons = document.querySelectorAll(`#kc-${moduleNum} .kc-option-btn`);
        buttons.forEach(btn => btn.disabled = false);
    }
}

// Allow user to retry knowledge check after incorrect answer (legacy support)
function tryKnowledgeCheckAgain(moduleNum) {
    const buttons = document.querySelectorAll(`#kc-${moduleNum} .kc-option-btn`);
    buttons.forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('selected', 'correct', 'incorrect');
    });
    const feedbackDiv = document.getElementById('kc-feedback-' + moduleNum);
    if (feedbackDiv) { feedbackDiv.className = 'feedback'; feedbackDiv.innerHTML = ''; }
} 


function updateProgress() {
    const hasQuiz = Boolean(window.courseData?.quiz?.questions?.length > 0);
    
    // Section-wise progress calculation
    // Count total sections across all modules + quiz as one component
    let totalSections = 0;
    let completedSectionCount = 0;
    
    const modules = window.courseData?.modules || [];
    for (let m = 0; m < modules.length; m++) {
        const moduleData = modules[m];
        const sections = moduleData?.content?.sections || [];
        const moduleNum = moduleData?.moduleNumber || (m + 1);
        
        if (sections.length > 0) {
            totalSections += sections.length;
            // Count completed sections for this module
            for (let s = 1; s <= sections.length; s++) {
                const sectionKey = `${moduleNum}.${s}`;
                if (sectionsCompleted[sectionKey]) {
                    completedSectionCount++;
                }
            }
        } else {
            // Module without sections counts as 1 unit
            totalSections += 1;
            if (modulesCompleted[moduleNum]) {
                completedSectionCount++;
            }
        }
    }
    
    // Add quiz as a component
    if (hasQuiz) {
        totalSections += 1;
        if (window.quizPassed) completedSectionCount++;
    }
    
    let progress = totalSections > 0 ? Math.round((completedSectionCount / totalSections) * 100) : 100;
    
    // Update main progress bar
    const mainProgressFill = document.getElementById('progressFill');
    if (mainProgressFill) {
        mainProgressFill.style.width = progress + '%';
    }
    
    // Update sidebar progress bar
    const sidebarProgressFill = document.getElementById('sidebarProgressFill');
    const sidebarProgressText = document.getElementById('sidebarProgressText');
    if (sidebarProgressFill) {
        sidebarProgressFill.style.width = progress + '%';
    }
    if (sidebarProgressText) {
        sidebarProgressText.textContent = progress + '% ' + window.uiLabels.pct_complete;
    }
    
    // Update sidebar section nav items to reflect completion
    updateSidebarSections();
    
    // Send xAPI progressed statement (Rise360 compatible)
    // Only send when progress actually changes to avoid flooding LRS
    if (xapiInitialized && progress !== window._lastReportedProgress) {
        window._lastReportedProgress = progress;
        sendStatement(VERBS.progressed, courseURI, document.title, 
            "Learner progressed to " + progress + "%", progress, null, 
            "http://adlnet.gov/expapi/activities/course");
    }
    
    if (progress >= 100) {
        trackCourseCompletion();
    }
}

// Update sidebar section nav items to show completion/active/locked states
function updateSidebarSections() {
    const modules = window.courseData?.modules || [];
    for (let m = 0; m < modules.length; m++) {
        const moduleData = modules[m];
        const moduleNum = moduleData?.moduleNumber || (m + 1);
        const sections = moduleData?.content?.sections || [];
        
        for (let s = 1; s <= sections.length; s++) {
            const sectionKey = `${moduleNum}.${s}`;
            const sectionNavItem = document.getElementById(`section-nav-${moduleNum}-${s}`);
            if (!sectionNavItem) continue;
            
            if (sectionsCompleted[sectionKey]) {
                sectionNavItem.classList.add('completed');
                sectionNavItem.classList.remove('active', 'locked');
            } else if (currentSection.module === moduleNum && currentSection.section === s) {
                sectionNavItem.classList.add('active');
                sectionNavItem.classList.remove('completed', 'locked');
            }
        }
    }
}

// Global fallback to ensure continue buttons always work
function initializeContinueButtonFallback() {
    // Check all continue buttons periodically and enable if section is visible
    setInterval(() => {
        document.querySelectorAll('.btn-continue').forEach(btn => {
            const btnId = btn.id;
            const match = btnId.match(/continue-(\\d+)-(\\d+)/);
            if (match) {
                const moduleNum = match[1];
                const sectionNum = match[2];
                const sectionId = `module-${moduleNum}-section-${sectionNum}`;
                const sectionEl = document.getElementById(sectionId);
                
                if (sectionEl && sectionEl.style.display !== 'none') {
                    // Check if button is still disabled after reasonable time
                    const trackingKey = `section_${moduleNum}_${sectionNum}_tracking`;
                    const loadTimeKey = trackingKey + '_loadTime';
                    const timeSinceLoad = Date.now() - (window[loadTimeKey] || Date.now());
                    
                    // If section visible for more than 8 seconds and button still disabled, force enable
                    if (btn.disabled && timeSinceLoad > 8000) {
                        const hasAudio = sectionEl.querySelector('audio') !== null;
                        const audio = sectionEl.querySelector('audio');
                        const audioOk = !hasAudio || (audio && audio.ended);
                        const kcOk = window[trackingKey] ? window[trackingKey].kcCompleted : true;
                        
                        // Force enable if audio is done, no audio exists, AND KC is completed
                        if (audioOk && kcOk) {
                            btn.disabled = false;
                            btn.classList.remove('disabled');
                            btn.style.opacity = '1';
                            btn.style.cursor = 'pointer';
                            btn.style.pointerEvents = 'auto';
                            console.log(`✅ Continue button FORCE ENABLED (fallback) for section ${moduleNum}.${sectionNum}`);
                        }
                    }
                }
            }
        });
    }, 2000); // Check every 2 seconds
}

function flipCard(cardId) {
    const card = document.getElementById(cardId);
    if (card) {
        card.classList.toggle('flipped');
    }
}

function downloadCertificate() {
    // Certificate download - placeholder
}

// Enhanced xAPI Tracking Functions
// Get learner information from URL params (set during initXAPI)
function getLearnerInfo() {
    // Use actor parsed from LMS launch URL (set in initXAPI)
    if (xapiActor) {
        return xapiActor;
    }
    // Try to get from LMS, fallback to defaults
    if (typeof window.learnerInfo !== 'undefined') {
        return window.learnerInfo;
    }
    // Last resort: try parsing from URL directly
    var actorParam = getUrlParam('actor');
    if (actorParam) {
        try {
            var parsed = JSON.parse(actorParam);
            // Normalize array fields to single values (SCORM Cloud format)
            if (Array.isArray(parsed.name)) parsed.name = parsed.name[0] || "";
            if (Array.isArray(parsed.account)) parsed.account = parsed.account[0] || {};
            if (Array.isArray(parsed.mbox)) parsed.mbox = parsed.mbox[0] || "";
            if (Array.isArray(parsed.mbox_sha1sum)) parsed.mbox_sha1sum = parsed.mbox_sha1sum[0] || "";
            if (Array.isArray(parsed.openid)) parsed.openid = parsed.openid[0] || "";
            // Rename SCORM Cloud's non-standard account field names
            if (parsed.account && typeof parsed.account === 'object') {
                if (parsed.account.accountServiceHomePage && !parsed.account.homePage) {
                    parsed.account.homePage = parsed.account.accountServiceHomePage;
                    delete parsed.account.accountServiceHomePage;
                }
                if (parsed.account.accountName && !parsed.account.name) {
                    parsed.account.name = parsed.account.accountName;
                    delete parsed.account.accountName;
                }
            }
            return parsed;
        } catch(e) {}
    }
    return {
        mbox: 'mailto:learner@example.com',
        name: 'Unknown Learner'
    };
}

// Get course ID from course data
function getCourseId() {
    if (window.courseData && window.courseData.course && window.courseData.course.id) {
        return window.courseData.course.id;
    }
    return 'course-1';
}

// Generate timestamp in ISO 8601 format
function getTimestamp() {
    return new Date().toISOString();
}

// Enhanced xAPI statement sender
function sendXAPIStatement(verb, objectType, objectId, options = {}) {
    if (!xapiInitialized || !xapiEndpoint) {
        return; // Fast exit to prevent 404s in standalone/preview mode
    }
    
    const learner = getLearnerInfo();
    const courseId = getCourseId();
    const timestamp = getTimestamp();
    
    // Map verb names to xAPI verb IDs
    const verbMap = {
        'completed': 'http://adlnet.gov/expapi/verbs/completed',
        'answered': 'http://adlnet.gov/expapi/verbs/answered',
        'viewed': 'http://adlnet.gov/expapi/verbs/viewed',
        'listened': 'http://adlnet.gov/expapi/verbs/listened',
        'paused': 'http://adlnet.gov/expapi/verbs/paused',
        'interacted': 'http://adlnet.gov/expapi/verbs/interacted',
        'experienced': 'http://adlnet.gov/expapi/verbs/experienced'
    };
    
    const verbId = verbMap[verb] || `http://adlnet.gov/expapi/verbs/${verb}`;
    const verbDisplay = verb.charAt(0).toUpperCase() + verb.slice(1);
    
    // Build object ID
    let finalObjectId;
    if (objectId) {
        // If objectId is provided and starts with http, use as-is
        if (objectId.startsWith('http')) {
            finalObjectId = objectId;
        } else {
            // Otherwise, construct from course context
            finalObjectId = `http://coursegen.ai/activities/${objectType}${objectId ? '-' + objectId : ''}`;
        }
    } else {
        finalObjectId = `http://coursegen.ai/activities/${objectType}`;
    }
    
    // Build statement with correct actor from LMS launch params
    const statement = {
        actor: learner,
        verb: {
            id: verbId,
            display: { 'en-US': verbDisplay }
        },
        object: {
            id: finalObjectId,
            objectType: options.objectType || 'Activity',
            definition: options.definition || {
                name: { 'en-US': objectType + (objectId ? ' ' + objectId : '') }
            }
        },
        timestamp: timestamp,
        
        // LMS-specific fields (EmpowerLMS / Hygiena requirement)
        portalId: lmsPortalId || null,
        studentID: lmsStudentID || null,
        subscriptionId: lmsSubscriptionId || null,
        identifier: lmsIdentifier || null,
        statementId: generateUUID()
    };
    
    // Add result if provided

    if (options.result !== undefined) {
        statement.result = options.result;
    }
    
    // CRITICAL: Add context with registration ID
    // This links statements to the learner's course attempt in the LMS
    statement.context = options.context || {};
    if (registrationId) {
        statement.context.registration = registrationId;
    }
    // Add grouping context if not already present
    if (!statement.context.contextActivities) {
        statement.context.contextActivities = {
            'grouping': [{
                'id': courseURI || window.location.href.split('?')[0],
                'objectType': 'Activity'
            }]
        };
    }
    
    // Send via ADL xAPIWrapper (official library handles auth, headers, actor)
    if (typeof ADL !== 'undefined' && ADL.XAPIWrapper && ADL.XAPIWrapper.testConfig()) {
        try {
            ADL.XAPIWrapper.sendStatement(statement, function(resp, obj) {
                if (resp && resp.status >= 200 && resp.status < 300) {
                    console.log('xAPI statement sent via ADL wrapper: ' + verbDisplay + ' (HTTP ' + resp.status + ')');
                } else {
                    console.error('xAPI statement FAILED via ADL wrapper: HTTP ' + (resp ? resp.status : '?') + ' - ' + (resp ? resp.responseText : 'no response'));
                }
            });
            console.log('xAPI statement queued via ADL wrapper:', statement);
        } catch (e) {
            console.error('Failed to send xAPI statement via ADL wrapper:', e);
        }
    } else if (xapiEndpoint) {
        // Fallback: direct XHR if ADL wrapper not available
        try {
            var xhr = new XMLHttpRequest();
            var stmtUrl = xapiEndpoint + 'statements';
            xhr.open('POST', stmtUrl, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-Experience-API-Version', '1.0.3');
            if (xapiAuth) {
                xhr.setRequestHeader('Authorization', xapiAuth);
            }
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        console.log('xAPI statement sent (fallback XHR): ' + verbDisplay + ' (HTTP ' + xhr.status + ')');
                    } else {
                        console.error('xAPI statement FAILED (fallback XHR): HTTP ' + xhr.status + ' - ' + xhr.responseText);
                    }
                }
            };
            xhr.send(JSON.stringify(statement));
            console.log('xAPI statement queued (fallback XHR):', statement);
        } catch (e) {
            console.error('Failed to send xAPI statement:', e);
        }
    } else {
        // No endpoint configured - log for debugging
        console.log('xAPI statement (no endpoint):', JSON.stringify(statement, null, 2));
    }
    
    // Also send to State API for LMS compatibility (EmpowerLMS / Hygiena)
    if (xapiEndpoint) {
        try {
            var stateUrl = xapiEndpoint + 'activities/state';
            var queryParams = [];
            
            queryParams.push('stateId=cumulative_time');
            queryParams.push('activityId=' + encodeURIComponent(courseURI || window.location.href.split('?')[0]));
            queryParams.push('agent=' + encodeURIComponent(JSON.stringify(learner)));
            
            if (registrationId) queryParams.push('registration=' + encodeURIComponent(registrationId));
            if (lmsSubscriptionId) queryParams.push('subscriptionId=' + encodeURIComponent(lmsSubscriptionId));
            if (lmsStudentID) queryParams.push('studentID=' + encodeURIComponent(lmsStudentID));
            if (lmsPortalId) queryParams.push('portalId=' + encodeURIComponent(lmsPortalId));
            if (lmsIdentifier) queryParams.push('identifier=' + encodeURIComponent(lmsIdentifier));
            
            stateUrl += '?' + queryParams.join('&');
            
            // Create simple state payload
            var stateData = {
                v: 2,
                d: [100, 111, 110, 101] 
            };
            
            var stateXhr = new XMLHttpRequest();
            stateXhr.open('PUT', stateUrl, true);
            stateXhr.setRequestHeader('Content-Type', 'application/json');
            stateXhr.setRequestHeader('X-Experience-API-Version', '1.0.3');
            if (xapiAuth) {
                stateXhr.setRequestHeader('Authorization', xapiAuth);
            }
            
            stateXhr.onreadystatechange = function() {
                if (stateXhr.readyState === 4) {
                    if (stateXhr.status >= 200 && stateXhr.status < 300) {
                        console.log('State API Update Success');
                    } else {
                        console.warn('State API Update Failed: ' + stateXhr.status);
                    }
                }
            };
            stateXhr.send(JSON.stringify(stateData));
        } catch(e) {
            console.error('Error sending State API update:', e);
        }
    }

    
    return statement;
}

// Track course completion
let courseCompletionTracked = false;
function trackCourseCompletion() {
    // Ensure NavBar shows 100% when explicitly marked complete
    const mainProgressFill = document.getElementById('progressFill');
    if (mainProgressFill) mainProgressFill.style.width = '100%';
    const sidebarProgressFill = document.getElementById('sidebarProgressFill');
    const sidebarProgressText = document.getElementById('sidebarProgressText');
    if (sidebarProgressFill) sidebarProgressFill.style.width = '100%';
    if (sidebarProgressText) sidebarProgressText.textContent = '100% ' + window.uiLabels.pct_complete;

    if (courseCompletionTracked) return;
    courseCompletionTracked = true;

    const courseId = getCourseId();
    const courseTitle = window.courseData?.course?.title || 'Course';
    const courseObjectId = `http://coursegen.ai/courses/${courseId}`;
    
    // Changed to passed from completed
    sendXAPIStatement('passed', 'course', courseObjectId, {
        objectType: 'Activity',
        definition: {
            type: 'http://adlnet.gov/expapi/activities/course',
            name: { 'en-US': courseTitle }
        },
        result: {
            success: true,
            completion: true
        }
    });
}

// Track image viewing
function trackImageViewed(imagePath) {
    // Construct full URL from image path
    const imageUrl = imagePath.startsWith('http') ? imagePath : 
                     (window.location.origin + '/' + imagePath);
    
    sendXAPIStatement('viewed', 'image', imageUrl, {
        objectType: 'Activity',
        definition: {
            type: 'http://activitystrea.ms/schema/1.0/image',
            name: { 'en-US': 'Image: ' + imagePath.split('/').pop() }
        },
        result: {
            success: true,
            completion: true
        }
    });
}

// Track audio listening
function trackAudioListened(audioPath, audioTitle) {
    const audioUrl = audioPath.startsWith('http') ? audioPath : 
                     (window.location.origin + '/' + audioPath);
    
    sendXAPIStatement('listened', 'audio', audioUrl, {
        objectType: 'Activity',
        definition: {
            type: 'http://activitystrea.ms/schema/1.0/audio',
            name: { 'en-US': audioTitle || ('Audio: ' + audioPath.split('/').pop()) }
        },
        result: {
            success: true,
            completion: true
        }
    });
}

// Track audio paused
function trackAudioPaused(audioPath, audioTitle) {
    const audioUrl = audioPath.startsWith('http') ? audioPath : 
                     (window.location.origin + '/' + audioPath);
    
    sendXAPIStatement('paused', 'audio', audioUrl, {
        objectType: 'Activity',
        definition: {
            type: 'http://activitystrea.ms/schema/1.0/audio',
            name: { 'en-US': audioTitle || ('Audio: ' + audioPath.split('/').pop()) }
        },
        result: {
            success: true,
            completion: false
        }
    });
}

// Track quiz question answered
function trackQuizQuestionAnswered(questionIndex, questionId, selectedAnswer, isCorrect) {
    const questionObjectId = `http://coursegen.ai/questions/${questionId || questionIndex}`;
    
    sendXAPIStatement('answered', 'question', questionObjectId, {
        objectType: 'Activity',
        definition: {
            type: 'http://adlnet.gov/expapi/activities/question',
            name: { 'en-US': 'Question ' + (questionIndex + 1) }
        },
        result: {
            response: selectedAnswer,
            score: {
                scaled: isCorrect ? 1 : 0
            },
            success: isCorrect,
            completion: true
        }
    });
}

// Initialize tracking for all media elements
document.addEventListener('DOMContentLoaded', function() {
    // Track images when they're viewed
    document.querySelectorAll('img[data-image-id]').forEach(img => {
        img.addEventListener('load', function() {
            const imageId = this.getAttribute('data-image-id');
            if (imageId) {
                trackImageViewed(imageId);
            }
        });
    });
    
    // Track audio interactions - set up after DOM is loaded
    function setupAudioTracking() {
        document.querySelectorAll('audio').forEach(audio => {
            // Get audio source - check data attribute first, then src, then source tag
            let audioSrc = audio.getAttribute('data-audio-path');
            if (!audioSrc) {
                audioSrc = audio.src || (audio.querySelector('source') && audio.querySelector('source').src);
            }
            let audioTitle = audio.getAttribute('data-audio-title') || null;
            
            if (audioSrc) {
                // Track when audio starts playing (listened)
                audio.addEventListener('play', function() {
                    // Stop all other audio elements to prevent overlap
                    document.querySelectorAll('audio').forEach(otherAudio => {
                        if (otherAudio !== audio && !otherAudio.paused) {
                            otherAudio.pause();
                            otherAudio.currentTime = 0;
                        }
                    });
                    trackAudioListened(audioSrc, audioTitle);
                });
                
                // Track when audio is paused
                audio.addEventListener('pause', function() {
                    if (!audio.ended) {
                        trackAudioPaused(audioSrc, audioTitle);
                    }
                });
                
                // Track when audio ends (completion)
                audio.addEventListener('ended', function() {
                    trackAudioListened(audioSrc); // Ensure completion is noted
                });
            }
        });
    }
    
    // Setup audio tracking immediately and after a delay to catch dynamically loaded audio
    setupAudioTracking();
    setTimeout(setupAudioTracking, 1000);
});

// Quiz navigation and management
let currentQuizQuestion = 0;
let quizQuestions = [];
let quizRetryCount = 0;
const MAX_QUIZ_RETRIES = 3;

function startQuiz() {
    const quiz = window.courseData?.quiz;
    if (!quiz || !quiz.questions) {
        console.error('Quiz data not found');
        return;
    }
    
    // On first attempt, shuffle questions
    quizQuestions = shuffleArray(quiz.questions);
    currentQuizQuestion = 0;
    
    // Reset retry count on quiz start (new attempt from intro)
    if (quizRetryCount === 0) {
        quizRetryCount = 0; // First attempt
    }
    
    // Hide quiz intro, show quiz section
    const quizIntro = document.getElementById('quizIntroSection');
    if (quizIntro) quizIntro.style.display = 'none';

    const quizSection = document.getElementById('quizSection');
    if (quizSection) quizSection.style.display = 'block';
    quizState = 'active';
    
    // Send xAPI attempted statement (Rise360 compatible)
    if (xapiInitialized) {
        const quizID = courseURI + "/quiz";
        sendStatement(VERBS.attempted, quizID, "Final Quiz", 
            "Learner started the quiz", null, null, 
            "http://adlnet.gov/expapi/activities/assessment");
    }
    
    // Build and display quiz questions
    const container = document.getElementById('quizSlideContainer');
    if (container) {
        container.innerHTML = '';
        quizQuestions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question-block';
            questionDiv.id = `quiz-q-${index}`;
            questionDiv.style.display = index === 0 ? 'block' : 'none';
            
            questionDiv.innerHTML = `
                <p class="question-number">${window.uiLabels.question_x_of_y.replace('{0}', index + 1).replace('{1}', quizQuestions.length)}</p>
                <p class="question-text">${escapeHtml(question.question || '')}</p>
                <div class="options">
                    ${Object.entries(question.options || {}).map(([key, value]) => `
                        <button class="kc-option-btn" id="quiz-q-${index}-${key}" onclick="selectQuizOption(${index}, '${key}')">
                            <span class="kc-option-label">${key}.</span>
                            <span class="kc-option-text">${escapeHtml(value)}</span>
                        </button>
                    `).join('')}
                </div>
                <div id="quiz-feedback-${index}" class="feedback"></div>
            `;
            
            container.appendChild(questionDiv);
        });
    }
    
    updateQuizProgress();
    enableQuizNext();

    // Reset navigation buttons for a fresh quiz attempt
    const prevBtn = document.getElementById('quizPrevBtn');
    const nextBtn = document.getElementById('quizNextBtn');
    if (prevBtn) prevBtn.style.display = 'none';
    if (nextBtn) {
        nextBtn.textContent = window.uiLabels.next_btn;
        nextBtn.onclick = nextQuizQuestion;
        nextBtn.disabled = true;
    }
}

function selectQuizOption(qIndex, key) {
    const btns = document.querySelectorAll('#quiz-q-' + qIndex + ' .kc-option-btn');
    if (btns.length > 0 && btns[0].disabled) return;
    
    btns.forEach(btn => btn.classList.remove('selected'));
    const selectedBtn = document.getElementById('quiz-q-' + qIndex + '-' + key);
    if (selectedBtn) selectedBtn.classList.add('selected');
    
    enableQuizNext();
}

function nextQuizQuestion() {
    const btns = document.querySelectorAll(`#quiz-q-${currentQuizQuestion} .kc-option-btn`);
    let selectedValue = null;
    let selectedBtn = null;
    btns.forEach(b => {
        if (b.classList.contains('selected')) {
            selectedValue = b.id.split('-').pop();
            selectedBtn = b;
        }
    });

    if (!selectedValue) {
        alert(window.uiLabels.select_answer);
        return;
    }
    
    // Check answer and show feedback
    const question = quizQuestions[currentQuizQuestion];
    const isCorrect = selectedValue === question.correctAnswer;
    const feedbackDiv = document.getElementById(`quiz-feedback-${currentQuizQuestion}`);
    
    // Disable buttons and show correctness
    btns.forEach(b => b.disabled = true);
    if (isCorrect) {
        selectedBtn.classList.add('correct');
    } else {
        selectedBtn.classList.add('incorrect');
    }
    
    if (feedbackDiv) {
        feedbackDiv.className = isCorrect ? 'feedback correct' : 'feedback incorrect';
        feedbackDiv.innerHTML = isCorrect 
            ? `<strong>${window.uiLabels.correct || 'Correct!'}</strong> ${question.feedback?.correct || ''}`
            : `<strong>${window.uiLabels.incorrect || 'Incorrect'}</strong> ${question.feedback?.incorrect || ''} <br/><button class="btn-secondary" onclick="tryQuizQuestionAgain(${currentQuizQuestion})">${window.uiLabels.try_again_title || 'Try Again'}</button>`;
    }
    
    // Track answer
    trackQuizQuestionAnswered(currentQuizQuestion, currentQuizQuestion + 1, selectedValue, isCorrect);
    
    // Move to next question
    if (currentQuizQuestion < quizQuestions.length - 1) {
        // Hide current question
        const currentQ = document.getElementById(`quiz-q-${currentQuizQuestion}`);
        if (currentQ) currentQ.style.display = 'none';
        
        currentQuizQuestion++;
        
        // Show next question
        const nextQ = document.getElementById(`quiz-q-${currentQuizQuestion}`);
        if (nextQ) nextQ.style.display = 'block';
        
        updateQuizProgress();
        enableQuizNext();
        
        // Show previous button if not on first question
        const prevBtn = document.getElementById('quizPrevBtn');
        if (prevBtn) prevBtn.style.display = currentQuizQuestion > 0 ? 'inline-block' : 'none';
        
        // Change next button to submit if last question
        const nextBtn = document.getElementById('quizNextBtn');
        if (nextBtn) {
            if (currentQuizQuestion === quizQuestions.length - 1) {
                nextBtn.textContent = window.uiLabels.submit_quiz;
                nextBtn.onclick = submitQuiz;
            } else {
                nextBtn.textContent = window.uiLabels.next_btn;
                nextBtn.onclick = nextQuizQuestion;
            }
        }
    } else {
        // Last question - submit quiz
        submitQuiz();
    }
}

function previousQuizQuestion() {
    if (currentQuizQuestion > 0) {
        // Hide current question
        const currentQ = document.getElementById(`quiz-q-${currentQuizQuestion}`);
        if (currentQ) currentQ.style.display = 'none';
        
        currentQuizQuestion--;
        
        // Show previous question
        const prevQ = document.getElementById(`quiz-q-${currentQuizQuestion}`);
        if (prevQ) prevQ.style.display = 'block';
        
        updateQuizProgress();
        enableQuizNext();
        
        // Show/hide previous button
        const prevBtn = document.getElementById('quizPrevBtn');
        if (prevBtn) prevBtn.style.display = currentQuizQuestion > 0 ? 'inline-block' : 'none';
        
        // Change next button text
        const nextBtn = document.getElementById('quizNextBtn');
        if (nextBtn) {
            nextBtn.textContent = window.uiLabels.next_btn;
            nextBtn.onclick = nextQuizQuestion;
        }
    }
}

function enableQuizNext() {
    const nextBtn = document.getElementById('quizNextBtn');
    if (nextBtn) {
        let hasSelected = false;
        document.querySelectorAll(`#quiz-q-${currentQuizQuestion} .kc-option-btn`).forEach(b => {
            if (b.classList.contains('selected')) hasSelected = true;
        });
        nextBtn.disabled = !hasSelected;
    }
}

function updateQuizProgress() {
    const progressFill = document.getElementById('quizProgressFill');
    const progressText = document.getElementById('quizProgressText');
    
    if (progressFill) {
        const progress = ((currentQuizQuestion + 1) / quizQuestions.length) * 100;
        progressFill.style.width = progress + '%';
    }
    
    if (progressText) {
        progressText.textContent = window.uiLabels.question_x_of_y.replace('{0}', currentQuizQuestion + 1).replace('{1}', quizQuestions.length);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Allow user to retry a single quiz question after an incorrect attempt
function tryQuizQuestionAgain(qIndex) {
    const btns = document.querySelectorAll(`#quiz-q-${qIndex} .kc-option-btn`);
    btns.forEach(b => {
        b.classList.remove('selected', 'correct', 'incorrect');
        b.disabled = false;
    });
    const feedbackDiv = document.getElementById('quiz-feedback-' + qIndex);
    if (feedbackDiv) { feedbackDiv.className = 'feedback'; feedbackDiv.innerHTML = ''; }
    const nextBtn = document.getElementById('quizNextBtn');
    if (nextBtn) nextBtn.disabled = true;
}

// Enhanced quiz submission with individual question tracking
function submitQuiz() {
    const quiz = window.courseData?.quiz;
    if (!quiz) return;
    
    let totalQuestions = quizQuestions.length;
    let correctAnswers = 0;
    
    quizQuestions.forEach((question, index) => {
        let selectedValue = null;
        document.querySelectorAll(`#quiz-q-${index} .kc-option-btn`).forEach(b => {
            if (b.classList.contains('selected')) selectedValue = b.id.split('-').pop();
        });
        
        if (!selectedValue) {
            // No answer selected - count as incorrect
            return;
        }
        
        quizAnswers[index] = selectedValue;
        const isCorrect = selectedValue === question.correctAnswer;
        
        // Track each question answer individually
        const questionId = question.questionNumber || (index + 1);
        trackQuizQuestionAnswered(index, questionId, selectedValue, isCorrect);
        
        if (isCorrect) {
            correctAnswers++;
        }
    });
    
    const scorePercentage = (correctAnswers / totalQuestions) * 100;

    const passed = scorePercentage >= 80;
    if (passed) {
        window.quizPassed = true;
    }

    // Send xAPI Statement for Quiz
    if (xapiInitialized) {
        const quizID = courseURI + "/quiz";
        const verb = passed ? VERBS.passed : VERBS.failed;
        const description = "Learner " + (passed ? "passed" : "failed") + " the final quiz.";
        
        // Use scorePercentage for raw score
        sendStatement(verb, quizID, "Final Quiz", description, Math.round(scorePercentage));
        console.log("Quiz completed. Score: " + Math.round(scorePercentage) + "%. Passed: " + passed);
    }
    
    // Hide quiz section and show results section
    document.getElementById('quizSection').style.display = 'none';
    document.getElementById('quizResultsSection').style.display = 'block';
    quizState = 'results';
    
    const resultsPage = document.getElementById('quizResultsPage');
    resultsPage.innerHTML = '<h3>' + window.uiLabels.quiz_results + '</h3><p>' + window.uiLabels.you_scored.replace('{0}', correctAnswers).replace('{1}', totalQuestions).replace('{2}', scorePercentage.toFixed(1)) + '</p>';
    
    if (scorePercentage >= 80) {
        resultsPage.innerHTML += '<div class="certificate-section"><h4>🎉 ' + window.uiLabels.congratulations + '</h4><p>' + window.uiLabels.passed_quiz_msg.replace('{0}', scorePercentage.toFixed(1)) + '</p><div class="certificate"><h3>' + window.uiLabels.certificate_title + '</h3><p>' + window.uiLabels.certificate_body + '</p></div></div>';
        
        // Unlock all modules in sidebar when course is completed
        unlockAllModules();
        
        // Clear saved progress since course is completed
        clearCourseProgress();
        
        setTimeout(() => {
            document.getElementById('quizResultsSection').style.display = 'none';
            document.getElementById('completionSection').style.display = 'block';
            updateProgress();
            
            // Track course completion when quiz is passed
            trackCourseCompletion();
        }, 3000);
    } else {
        const retriesLeft = MAX_QUIZ_RETRIES - quizRetryCount;
        let tryAgainContent = '<div class="try-again-section"><h4>' + window.uiLabels.try_again_title + '</h4><p>' + window.uiLabels.try_again_msg.replace('{0}', scorePercentage.toFixed(1)) + '</p>';
        
        if (retriesLeft > 0) {
            tryAgainContent += '<p style="margin: 15px 0; font-size: 14pt; color: #ff9800;"><strong>' + window.uiLabels.attempts_remaining.replace('{0}', retriesLeft).replace('{1}', MAX_QUIZ_RETRIES) + '</strong></p>';
            tryAgainContent += '<button class="btn-primary" onclick="resetQuiz()">' + window.uiLabels.try_again_title + '</button>';
        } else {
            tryAgainContent += '<p style="margin: 15px 0; font-size: 14pt; color: #d32f2f;"><strong>❌ ' + window.uiLabels.no_attempts.replace('{0}', MAX_QUIZ_RETRIES) + '</strong></p>';
            tryAgainContent += '<p>' + window.uiLabels.contact_instructor + '</p>';
        }
        
        tryAgainContent += '</div>';
        resultsPage.innerHTML += tryAgainContent;
    }
    
    window.scrollTo(0, 0);
}

// Shuffle array function (Fisher-Yates algorithm)
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

function resetQuiz() {
    // Increment retry count
    quizRetryCount++;

    // Check if retries exceeded
    if (quizRetryCount > MAX_QUIZ_RETRIES) {
        alert(window.uiLabels.no_attempts.replace('{0}', MAX_QUIZ_RETRIES) + ' ' + window.uiLabels.contact_instructor);
        return;
    }

    // Clear all quiz answers and reset counters
    quizAnswers = [];
    currentQuizQuestion = 0;

    // Shuffle quiz questions for each retry
    const quiz = window.courseData?.quiz;
    if (quiz && quiz.questions) {
        quizQuestions = shuffleArray(quiz.questions);
    }

    // Hide results section if present
    const resultsSection = document.getElementById('quizResultsSection');
    if (resultsSection) resultsSection.style.display = 'none';

    // Start the quiz immediately with newly shuffled questions (rebuilds DOM)
    startQuiz();

    // Scroll to top
    window.scrollTo(0, 0);
}

// Exit Course - close window or navigate away
function exitCourse() {
    // Try to close the window (works if opened by script)
    if (window.opener || window.parent !== window) {
        window.close();
    }
    // Fallback: try SCORM/xAPI exit
    if (typeof ADL !== 'undefined' && ADL.XAPIWrapper) {
        try { ADL.XAPIWrapper.log('Course exited'); } catch(e) {}
    }
    
    // Clear the screen and show a definitive "Full Page Finished" message
    document.body.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; background: linear-gradient(180deg, #f0f7ff 0%, #ffffff 100%); width: 100%; text-align: center; font-family: 'Roboto', sans-serif;">
            <div style="width: 100px; height: 100px; border-radius: 50%; background: #e8f5e9; color: #4caf50; font-size: 50px; display: flex; align-items: center; justify-content: center; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                &#10003;
            </div>
            <h1 style="color: #333; font-size: 2rem; margin-bottom: 15px;">You have successfully finished the course!</h1>
            <p style="color: #666; font-size: 1.2rem;">Your progress has been saved.</p>
            <p style="color: #888; margin-top: 20px;">You may safely close this window or tab.</p>
        </div>
    `;
}


