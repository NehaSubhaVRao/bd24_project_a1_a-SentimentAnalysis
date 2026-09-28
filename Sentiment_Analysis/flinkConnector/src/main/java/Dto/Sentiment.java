package Dto;

import lombok.Data;

import java.sql.Timestamp;
import java.time.LocalDateTime;

@Data
public class Sentiment {
    private String id;
    private String author;
    private Timestamp created_utc;
    private String body;
    private int score;
    private String subreddit;
    private int controversiality;
    private String label;


    // Default constructor
    public Sentiment() {
    }

    public Sentiment(String id, String author, Timestamp createdUtc, String body, int score, String subreddit, int controversiality, String label) {
        this.id = id;
        this.author = author;
        this.created_utc = createdUtc;
        this.body = body;
        this.score = score;
        this.subreddit = subreddit;
        this.controversiality = controversiality;
        this.label = label;
    }

    // Getters and setters

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }

    public Timestamp getCreatedUtc() { return created_utc; }
    public void setCreatedUtc(Timestamp createdUtc) { this.created_utc = createdUtc; }

    public String getBody() { return body; }
    public void setBody(String body) { this.body = body; }

    public int getScore() { return score; }
    public void setScore(int score) { this.score = score; }

    public String getSubreddit() { return subreddit; }
    public void setSubreddit(String subreddit) { this.subreddit = subreddit; }

    public int getControversiality() { return controversiality; }
    public void setControversiality(int controversiality) { this.controversiality = controversiality; }

    public String getlabel() { return label; }
    public void setlabel(String label) { this.label = label; }

    public void transformLabel() {
        if ("Positive".equalsIgnoreCase(this.label)) {
            this.label = "1";
        } else if ("Negative".equalsIgnoreCase(this.label)) {
            this.label = "0";
        }
    }
}