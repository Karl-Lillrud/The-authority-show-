  
  // Mic Function
  const micBtn = document.getElementById("micToggle");
  const micIcon = document.getElementById("micIcon");

  let isMuted = false;

  micBtn.addEventListener("click", () => {
    isMuted = !isMuted;

    // Swap image
    micIcon.src = isMuted ? "../Icons/MicMuted.png" : "../Icons/Mic.png";
    micIcon.alt = isMuted ? "mic muted" : "mic";

    // Optional: add a class for styling if needed
    micBtn.classList.toggle("muted", isMuted);
  });

  //Cards functiunallity
  let participants = [];

  function addParticipant(participant) {
    participants.push(participant);
    renderParticipants();
  }

  function removeParticipant(name) {
    participants = participants.filter(p => p.name !== name);
    renderParticipants();
  }

  function renderParticipants() {
    const container = document.getElementById("meetingcontainer");
    container.innerHTML = '';

    const maxVisible = 12;

    if (participants.length <= maxVisible) {
      // Show all participants directly
      participants.forEach(p => {
        const card = createParticipantCard(p);
        container.appendChild(card);
      });
    } else {
      // Show first 11 participants
      const visibleParticipants = participants.slice(0, maxVisible - 1);
      visibleParticipants.forEach(p => {
        const card = createParticipantCard(p);
        container.appendChild(card);
      });

      // Add the +X card instead of 12th participant
      const overflowCount = participants.length - (maxVisible - 1);
      const overCard = document.createElement("div");
      overCard.className = "card over-limit";
      overCard.innerHTML = `<h2>+${overflowCount}</h2>`;
      container.appendChild(overCard);
    }
    document.getElementById("userCount").textContent = participants.length;
  }

  function createParticipantCard(p) {
    const card = document.createElement("div");
    card.className = "card";
  
    if (p.stream) {
      const video = document.createElement("video");
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      video.srcObject = p.stream;
      video.style.width = "100%";
      video.style.borderRadius = "8px";
      card.appendChild(video);
    } else if (p.image) {
      const wrapper = document.createElement("div");
      wrapper.className = "image-wrapper";
  
      const img = document.createElement("img");
      img.src = p.image;
      img.alt = p.name;
  
      // Fullscreen button
      const button = document.createElement("button");
      button.className = "fullscreen-btn";
  
      const toggleFullscreen = (elem) => {
        if (!document.fullscreenElement) {
          elem.requestFullscreen?.() || elem.webkitRequestFullscreen?.() || elem.msRequestFullscreen?.();
        } else {
          document.exitFullscreen?.() || document.webkitExitFullscreen?.() || document.msExitFullscreen?.();
        }
      };
  
      img.addEventListener("click", () => toggleFullscreen(img));
      button.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleFullscreen(img);
      });
  
      wrapper.appendChild(img);
      wrapper.appendChild(button);
      card.appendChild(wrapper);
    } else {
      const name = document.createElement("h2");
      name.textContent = p.name;
      card.appendChild(name);
    }
  
    return card;
  }
  


  // Example usage
  addParticipant({ name: 'Random User 1', image: '../Icons/Person1.jpg' });
  addParticipant({ name: 'Random User 2', image: '../Icons/Person2.jpg' });
  addParticipant({ name: 'Random User 3', image: '../Icons/Person3.jpg' });
  addParticipant({ name: 'Random User 4', image: '../Icons/Person4.jpg' });
  addParticipant({ name: 'Random User 5', image: '../Icons/Person5.jpg' });
  addParticipant({ name: 'Random User 6', image: '../Icons/Person6.jpg' });
  addParticipant({ name: 'Random User 7', image: '../Icons/Person7.jpg' });
  addParticipant({ name: 'Random User 8', image: '../Icons/Person8.jpg' });
  addParticipant({ name: 'Random User 9', image: '../Icons/Person9.jpg' });
  addParticipant({ name: 'Random User 9' });
  addParticipant({ name: 'Random User 9' });
  addParticipant({ name: 'Random User 9' });

  // Add more participants as needed...
  

  //Sidebar functionallity
  const sidebar = document.getElementById('sidebar');
  const sidebarTitle = document.getElementById('sidebarTitle');
  const sidebarContent = document.getElementById('sidebarContent');
  const meetingContainer = document.getElementById('meetingcontainer');
  const userCount = document.getElementById("userCount");
  let users = participants;


  let currentPanel = null;

  const panelData = {
    users: {
      title: "Participants",
      content: () => {
        userCount.textContent = users.length;
        const wrapper = document.createElement('div');
        users.forEach(user => {
          const div = document.createElement('div');
          div.textContent = user.name || "Unnamed User";
          wrapper.appendChild(div);
        });
        return wrapper;
      }
    },
    chat: {
      title: "Chat",
      content: () => {
        const currentUser = "You"; 
    
        const chatSection = document.createElement("div");
        chatSection.className = "chat-section";
    
        const chatMessages = document.createElement("div");
        chatMessages.className = "chat-messages";
        chatMessages.id = "chatMessages";
    
        const chatInputDiv = document.createElement("div");
        chatInputDiv.className = "chat-input";
    
        const input = document.createElement("input");
        input.type = "text";
        input.id = "chatInput";
        input.placeholder = "Type a message...";
    
        const sendBtn = document.createElement("button");
        sendBtn.id = "sendBtn";
        sendBtn.textContent = "Send";
    
        // Reusable function to add a message
        function addChatMessage(user, text) {
          const msgDiv = document.createElement("div");
          msgDiv.className = "chat-message";
    
          if (user === currentUser) {
            msgDiv.classList.add("self");
          } else {
            msgDiv.classList.add("other");
          }
    
          msgDiv.textContent = `${user}: ${text}`;
          chatMessages.appendChild(msgDiv);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    
        sendBtn.addEventListener("click", () => {
          const message = input.value.trim();
          if (message) {
            addChatMessage(currentUser, message); // You sending a message
            input.value = "";
          }
        });
    
        input.addEventListener("keydown", (e) => {
          if (e.key === "Enter") sendBtn.click();
        });
    
        chatInputDiv.appendChild(input);
        chatInputDiv.appendChild(sendBtn);
        chatSection.appendChild(chatMessages);
        chatSection.appendChild(chatInputDiv);
        return chatSection;
      }
    },        
    room: {
      title: "Room",
      content: () => {
        const roomDiv = document.createElement('div');
        roomDiv.className = "room-controls";
    
        const statusText = document.createElement('p');
        statusText.id = "roomStatus";
        statusText.textContent = "No room created.";
        roomDiv.appendChild(statusText);
    
        const createBtn = document.createElement('button');
        createBtn.textContent = "Create Room";
        createBtn.onclick = () => {
          statusText.textContent = "Room created.";
        };
    
        const joinBtn = document.createElement('button');
        joinBtn.textContent = "Join Room";
        joinBtn.onclick = () => {
          statusText.textContent = "Joined existing room.";
        };
    
        const removeBtn = document.createElement('button');
        removeBtn.textContent = "Remove Room";
        removeBtn.onclick = () => {
          statusText.textContent = "Room removed.";
        };
    
        // Add buttons to container
        roomDiv.appendChild(createBtn);
        roomDiv.appendChild(joinBtn);
        roomDiv.appendChild(removeBtn);
    
        return roomDiv;
      }
    },    
    share: {
      title: "Share",
      content: () => {
        const shareDiv = document.createElement('div');
        shareDiv.className = "share-controls";
    
        const title = document.createElement('h3');
        title.textContent = "Sharing Options";
        shareDiv.appendChild(title);
    
        // Share Screen Button
        const screenBtn = document.createElement('button');
        screenBtn.textContent = "Share Your Screen";
        screenBtn.onclick = () => {
          alert("Screen sharing started (simulated).");
        };
    
        // Share Video Link Button
        const videoBtn = document.createElement('button');
        videoBtn.textContent = "Share Video Link";
        videoBtn.onclick = () => {
          const link = prompt("Paste your video link here:");
          if (link) alert(`Video link shared: ${link}`);
        };
    
        // File Upload
        const fileLabel = document.createElement('label');
        fileLabel.textContent = "Upload a File:";
        const fileInput = document.createElement('input');
        fileInput.type = "file";
        fileInput.onchange = () => {
          if (fileInput.files.length > 0) {
            alert(`File selected: ${fileInput.files[0].name}`);
          }
        };
    
        shareDiv.appendChild(screenBtn);
        shareDiv.appendChild(videoBtn);
        shareDiv.appendChild(fileLabel);
        shareDiv.appendChild(fileInput);
    
        return shareDiv;
      }
    },
    settings: {
      title: "Settings",
      content: () => {
        const settingsDiv = document.createElement('div');
    
        const sections = [
          {
            title: "Video Settings",
            content: `
              <label for="cameraSelect">Camera:
                <select id="cameraSelect">
                  <option>Default</option>
                </select>
              </label>
              <br/><br/>
              <label>Camera Preview:</label>
              <video id="cameraPreview" autoplay muted playsinline style="width: 100%; max-height: 200px; border-radius: 8px; background: #000;"></video>
            `
          },
          {
            title: "Audio Settings",
            content: `
              <label>Microphone:
                <select id="micSelect">
                  <option>Default</option>
                </select>
              </label>
            `
          },
          {
            title: "Display Options",
            content: `
              <label>
                <input type="checkbox" id="showParticipantNames" checked />
                Show participant names
              </label>
            `
          },
          {
            title: "Performance",
            content: `
              <label>
                Video bitrate:
                <input type="range" min="500" max="5000" step="100" value="2500" id="bitrateSlider" />
                <span id="bitrateLabel">2500 kbps</span>
              </label>
            `
          },
          {
            title: "Notifications",
            content: `
              <label>
                <input type="checkbox" id="notifJoin" checked />
                Notify when someone joins
              </label><br/>
              <label>
                <input type="checkbox" id="notifMessages" checked />
                Notify on new chat messages
              </label>
            `
          }
        ];

        //Video settings

        let currentStream = null;

        function startCameraPreview(deviceId) {
          if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
          }

          navigator.mediaDevices.getUserMedia({
            video: { deviceId: { exact: deviceId } }
          }).then(stream => {
            currentStream = stream;
            const video = document.getElementById("cameraPreview");
            if (video) {
              video.srcObject = stream;
            }
          }).catch(err => {
            console.error("Error accessing camera:", err);
          });
        }

        function populateCameraOptions() {
          const select = document.getElementById("cameraSelect");
          if (!select) return;

          navigator.mediaDevices.enumerateDevices().then(devices => {
            const cameras = devices.filter(d => d.kind === "videoinput");

            select.innerHTML = ""; 

            cameras.forEach((device, index) => {
              const option = document.createElement("option");
              option.value = device.deviceId;
              option.text = device.label || `Camera ${index + 1}`;
              select.appendChild(option);
            });

            if (cameras.length > 0) {
              startCameraPreview(cameras[0].deviceId);
            }

            select.addEventListener("change", () => {
              startCameraPreview(select.value);
            });
          });
        }

        // Call this after the DOM is fully built
        setTimeout(populateCameraOptions, 0);  


        sections.forEach((sec, index) => {
          const section = document.createElement('div');
          section.classList.add('settings-section');
    
          const header = document.createElement('h4');
          header.textContent = sec.title;
          header.style.cursor = "pointer";
          header.addEventListener('click', () => {
            content.classList.toggle('hidden');
          });
    
          const content = document.createElement('div');
          content.innerHTML = sec.content;
          content.classList.add('section-content');
    
          if (index !== 0) content.classList.add('hidden'); // collapse all but first
    
          section.appendChild(header);
          section.appendChild(content);
          settingsDiv.appendChild(section);
        });
    
        // Bitrate label update
        settingsDiv.addEventListener('input', e => {
          if (e.target.id === 'bitrateSlider') {
            settingsDiv.querySelector('#bitrateLabel').textContent = `${e.target.value} kbps`;
          }
        });
    
        return settingsDiv;
      }
    }    
  };

  function toggleSidebar(panelKey) {
    if (currentPanel === panelKey && sidebar.classList.contains('visible')) {
      sidebar.classList.remove('visible');
      meetingContainer.classList.remove('shrinked');
      currentPanel = null;
    } else {
      const panel = panelData[panelKey];
      if (panel) {
        sidebarTitle.textContent = panel.title;
        sidebarContent.innerHTML = '';
        sidebarContent.appendChild(panel.content());
        sidebar.classList.add('visible');
        meetingContainer.classList.add('shrinked');
        currentPanel = panelKey;
      }
    }
  }

  
  document.querySelector('.btn1').addEventListener('click', () => toggleSidebar('users'));
  document.querySelector('.btn2').addEventListener('click', () => toggleSidebar('chat'));
  document.querySelector('.btn3').addEventListener('click', () => toggleSidebar('room'));
  document.querySelector('.btn6').addEventListener('click', () => toggleSidebar('share'));
  document.querySelector('.btn7').addEventListener('click', () => toggleSidebar('settings'));

  document.querySelectorAll('.image-wrapper img').forEach(img => {
    img.addEventListener('click', () => {
      if (img.requestFullscreen) {
        img.requestFullscreen();
      } else if (img.webkitRequestFullscreen) { /* Safari */
        img.webkitRequestFullscreen();
      } else if (img.msRequestFullscreen) { /* IE11 */
        img.msRequestFullscreen();
      }
    });
  });


  document.addEventListener("DOMContentLoaded", () => {
    window.addEventListener('DOMContentLoaded', (event) => {
    // Retrieve user data from localStorage
    const userData = JSON.parse(localStorage.getItem("currentUser"));
    const hasCamera = localStorage.getItem("hasCamera") === "true";
    const hasMic = localStorage.getItem("hasMic") === "true";
  
    // Show the username or do any further setup with the user data
    const username = userData.name;
    console.log("User found:", username);
    
    // Optionally, update the UI to display the username
    document.getElementById("usernameDisplay").textContent = username;
  
    // If you want to automatically enable camera and mic preview based on saved state
    if (hasCamera) {
      console.log("Camera available!");
      // Start camera preview or other relevant actions here
    }
  
    if (hasMic) {
      console.log("Mic available!");
      // Initialize mic or related actions here
    }
    });
  });
  
  
  
  