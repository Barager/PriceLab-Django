var hiddenClass = 'hidden';
var shownClass = 'toggled-from-hidden';

function experimentSectionHover() {
    var children = this.children;
    for(var i = 0; i < children.length; i++) {
        var child = children[i];
        if (child.className === hiddenClass) {
            child.className = shownClass;
        }
    }
}

function experimentSectionEndHover() {
    var children = this.children;
    for(var i = 0; i < children.length; i++) {
        var child = children[i];
        if (child.className === shownClass) {
            child.className = hiddenClass;
        }
    }
}

(function() {
    var experimentSections = document.getElementsByClassName('experimentname');
    for(var i = 0; i < experimentSections.length; i++) {
        experimentSections[i].addEventListener('mouseover', experimentSectionHover);
        experimentSections[i].addEventListener('mouseout', experimentSectionEndHover);
    }
}());


