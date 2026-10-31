// Existing sermon content retained for direct sermon links.

const sermonData = {
  sample1: {
    title: "True Fasting",
    date: "December 29, 2016",
    preacher: "Pastor Niranjan",
    description:
      "As a church we sought the face of the Lord in fasting for a week.. But it was good for God to speak to us through Pastor Niranjan.. He reminded us of the true meaning of fasting...",
    youtubeId: "CaTb2JoALNw", // Replace with actual YouTube video ID
    audioFile: null, // Or null if no file
    audioLink: null, // Or null if no link
  },
  sample2: {
    title: "God is in the boat",
    date: "August 13, 2016",
    preacher: "Pastor Robert Gallagher",
    description:
      "A biblical exegesis of Mark 4: 35-41 .. The story exists to remind us that God is in the boat with us, and all we need to do is have some faith that he would take us to the other side as he promised!!! Watch, listen and be blessed!",
    youtubeId: "kziS51dikY0", // Replace with actual YouTube video ID
    audioFile: null,
    audioLink: null,
  },
  sample3: {
    title: "Sermon Excerpt - Truth Lovers",
    date: "July 10, 2026",
    preacher: "Pastor Nathanael Somanathan",
    description:
      "Seeking for a reformation within tamil christian circles, with a resurgence of Gospel centred truth and sound doctrine!!",
    youtubeId: "CyMZ_CJ4Vjo", // No video
    audioFile: null,
    audioLink: null,
  },
};

function openSermon(sermonKey) {
  const sermon = sermonData[sermonKey];
  if (!sermon) return;

  const modal = document.getElementById("sermonModal");

  // Set title and metadata
  document.getElementById("sermonTitle").textContent = sermon.title;
  document.getElementById("sermonDate").innerHTML =
    `<i class="fas fa-calendar"></i> ${sermon.date}`;
  document.getElementById("sermonPreacher").innerHTML =
    `<i class="fas fa-user"></i> ${sermon.preacher}`;
  document.getElementById("sermonDescription").textContent = sermon.description;

  // Clear previous content
  document.getElementById("sermonVideoContainer").innerHTML = "";
  document.getElementById("sermonAudioContainer").innerHTML = "";

  // Add YouTube video if available
  if (sermon.youtubeId) {
    const videoHTML = `
            <div class="video-container">
                <iframe
                    src="https://www.youtube.com/embed/${sermon.youtubeId}?autoplay=1"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
        `;
    document.getElementById("sermonVideoContainer").innerHTML = videoHTML;
  }

  // Add audio player if available
  if (sermon.audioFile || sermon.audioLink) {
    let audioHTML = '<div class="audio-player">';
    audioHTML += '<h3><i class="fas fa-headphones"></i> Listen to Audio</h3>';

    // Add audio player if file is available
    if (sermon.audioFile) {
      audioHTML += `
                <audio controls>
                    <source src="${sermon.audioFile}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            `;
    }

    // Add download/external links
    audioHTML += '<div class="audio-links">';

    if (sermon.audioFile) {
      audioHTML += `
                <a href="${sermon.audioFile}" download class="audio-link">
                    <i class="fas fa-download"></i> Download Audio
                </a>
            `;
    }

    if (sermon.audioLink) {
      audioHTML += `
                <a href="${sermon.audioLink}" target="_blank" class="audio-link">
                    <i class="fab fa-google-drive"></i> Listen on Google Drive
                </a>
            `;
    }

    audioHTML += "</div></div>";
    document.getElementById("sermonAudioContainer").innerHTML = audioHTML;
  }

  // Show modal
  modal.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeSermon() {
  const modal = document.getElementById("sermonModal");
  modal.classList.remove("active");
  document.body.style.overflow = "auto";

  // Stop video playback
  const videoContainer = document.getElementById("sermonVideoContainer");
  videoContainer.innerHTML = "";
}

// Close sermon modal when clicking outside
document.getElementById("sermonModal")?.addEventListener("click", function (e) {
  if (e.target === this) {
    closeSermon();
  }
});
